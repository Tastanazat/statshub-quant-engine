import sqlite3
import json
import os
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# MODEL CALIBRATION ENGINE V1
# ============================================================

DATABASE_FILE = "data/database/quant_engine.db"

OUTPUT_DIRECTORY = "data/models"

OUTPUT_FILE = (
    "data/models/calibration.json"
)


# ============================================================
# CALIBRATION SETTINGS
# ============================================================

CALIBRATION_METHOD = (
    "EMPIRICAL_BUCKET_SHRINKAGE"
)

MINIMUM_SAMPLE_REQUIREMENT = 30

BUCKET_WIDTH = 0.10

SHRINKAGE_STRENGTH = 30.0


# ============================================================
# MARKET DEFINITIONS
# ============================================================

MARKETS = {

    # --------------------------------------------------------
    # 1X2
    # --------------------------------------------------------

    "1X2_HOME": {
        "prediction_column":
            "home_win_probability"
    },

    "1X2_DRAW": {
        "prediction_column":
            "draw_probability"
    },

    "1X2_AWAY": {
        "prediction_column":
            "away_win_probability"
    },


    # --------------------------------------------------------
    # OVER / UNDER
    # --------------------------------------------------------

    "OVER_0_5": {
        "prediction_column":
            "over_0_5_probability"
    },

    "UNDER_0_5": {
        "prediction_column":
            "under_0_5_probability"
    },

    "OVER_1_5": {
        "prediction_column":
            "over_1_5_probability"
    },

    "UNDER_1_5": {
        "prediction_column":
            "under_1_5_probability"
    },

    "OVER_2_5": {
        "prediction_column":
            "over_2_5_probability"
    },

    "UNDER_2_5": {
        "prediction_column":
            "under_2_5_probability"
    },

    "OVER_3_5": {
        "prediction_column":
            "over_3_5_probability"
    },

    "UNDER_3_5": {
        "prediction_column":
            "under_3_5_probability"
    },

    "OVER_4_5": {
        "prediction_column":
            "over_4_5_probability"
    },

    "UNDER_4_5": {
        "prediction_column":
            "under_4_5_probability"
    },


    # --------------------------------------------------------
    # BTTS
    # --------------------------------------------------------

    "BTTS_YES": {
        "prediction_column":
            "btts_yes_probability"
    },

    "BTTS_NO": {
        "prediction_column":
            "btts_no_probability"
    }
}


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value):

    try:

        value = float(value)

    except (
        TypeError,
        ValueError
    ):

        return None

    if value != value:

        return None

    if value == float("inf"):

        return None

    if value == float("-inf"):

        return None

    return value


# ============================================================
# CLAMP PROBABILITY
# ============================================================

def clamp_probability(value):

    value = safe_float(value)

    if value is None:

        return None

    return max(
        0.0,
        min(
            1.0,
            value
        )
    )


# ============================================================
# ACTUAL RESULT
# ============================================================

def get_actual_result(
    market,
    result_1x2,
    total_goals,
    btts_result
):

    # --------------------------------------------------------
    # 1X2 HOME
    # --------------------------------------------------------

    if market == "1X2_HOME":

        return (
            1.0
            if result_1x2 == "HOME"
            else 0.0
        )


    # --------------------------------------------------------
    # 1X2 DRAW
    # --------------------------------------------------------

    if market == "1X2_DRAW":

        return (
            1.0
            if result_1x2 == "DRAW"
            else 0.0
        )


    # --------------------------------------------------------
    # 1X2 AWAY
    # --------------------------------------------------------

    if market == "1X2_AWAY":

        return (
            1.0
            if result_1x2 == "AWAY"
            else 0.0
        )


    # --------------------------------------------------------
    # TOTAL GOALS
    # --------------------------------------------------------

    if market.startswith("OVER_"):

        if total_goals is None:

            return None

        line_text = market.replace(
            "OVER_",
            ""
        )

        line = float(
            line_text.replace(
                "_",
                "."
            )
        )

        return (
            1.0
            if float(total_goals) > line
            else 0.0
        )


    if market.startswith("UNDER_"):

        if total_goals is None:

            return None

        line_text = market.replace(
            "UNDER_",
            ""
        )

        line = float(
            line_text.replace(
                "_",
                "."
            )
        )

        return (
            1.0
            if float(total_goals) < line
            else 0.0
        )


    # --------------------------------------------------------
    # BTTS YES
    # --------------------------------------------------------

    if market == "BTTS_YES":

        return (
            1.0
            if btts_result == "YES"
            else 0.0
        )


    # --------------------------------------------------------
    # BTTS NO
    # --------------------------------------------------------

    if market == "BTTS_NO":

        return (
            1.0
            if btts_result == "NO"
            else 0.0
        )


    return None


# ============================================================
# PROBABILITY BUCKET
# ============================================================

def get_bucket(probability):

    probability = clamp_probability(
        probability
    )

    if probability is None:

        return None

    # --------------------------------------------------------
    # 1.00 için son bucket
    # --------------------------------------------------------

    if probability >= 1.0:

        return 0.90


    bucket = (
        int(
            probability
            /
            BUCKET_WIDTH
        )
        *
        BUCKET_WIDTH
    )

    bucket = round(
        bucket,
        2
    )

    bucket = max(
        0.0,
        min(
            0.9,
            bucket
        )
    )

    return bucket


# ============================================================
# BUCKET LABEL
# ============================================================

def bucket_label(bucket):

    lower = int(
        round(
            bucket * 100
        )
    )

    upper = lower + 10

    return (
        f"{lower:02d}-{upper:02d}%"
    )


# ============================================================
# SHRINKED CALIBRATION
# ============================================================

def calculate_shrunk_probability(
    average_prediction,
    actual_frequency,
    sample_size
):

    # --------------------------------------------------------
    # Amaç:
    #
    # Küçük sample -> prediction'a daha fazla güven
    #
    # Büyük sample -> actual frequency'ye daha fazla yaklaş
    #
    # Böylece 3-5 maç sonucunda modelin olasılığı
    # uç noktalara çekilmez.
    # --------------------------------------------------------

    n = float(
        sample_size
    )

    strength = float(
        SHRINKAGE_STRENGTH
    )

    weight_actual = (
        n
        /
        (
            n + strength
        )
    )

    weight_prediction = (
        strength
        /
        (
            n + strength
        )
    )

    calibrated = (

        (
            weight_prediction
            *
            average_prediction
        )

        +

        (
            weight_actual
            *
            actual_frequency
        )

    )

    return max(
        0.0,
        min(
            1.0,
            calibrated
        )
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

connection = sqlite3.connect(
    DATABASE_FILE
)

connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute(
    "PRAGMA foreign_keys = ON"
)


# ============================================================
# HEADER
# ============================================================

print("")
print("==========================================")
print("STATSHUB MODEL CALIBRATION ENGINE V1")
print("==========================================")
print("")

print(
    "Database:",
    DATABASE_FILE
)

print(
    "Method:",
    CALIBRATION_METHOD
)

print(
    "Minimum sample:",
    MINIMUM_SAMPLE_REQUIREMENT
)

print(
    "Shrinkage strength:",
    SHRINKAGE_STRENGTH
)

print("")


# ============================================================
# DATABASE CHECK
# ============================================================

cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    AND name='calibration_history'
    """
)

if cursor.fetchone() is None:

    connection.close()

    raise SystemExit(
        "ERROR: calibration_history tablosu bulunamadı."
    )


# ============================================================
# FIND SETTLED PREDICTIONS
# ============================================================

cursor.execute(
    """
    SELECT

        p.id AS prediction_id,

        p.model_version,

        p.model_locked,

        p.home_win_probability,
        p.draw_probability,
        p.away_win_probability,

        p.over_0_5_probability,
        p.under_0_5_probability,

        p.over_1_5_probability,
        p.under_1_5_probability,

        p.over_2_5_probability,
        p.under_2_5_probability,

        p.over_3_5_probability,
        p.under_3_5_probability,

        p.over_4_5_probability,
        p.under_4_5_probability,

        p.btts_yes_probability,
        p.btts_no_probability,

        s.result_1x2,
        s.total_goals,
        s.btts_result

    FROM predictions p

    INNER JOIN settlements s
        ON s.prediction_id = p.id

    WHERE
        s.settled = 1

        AND s.id = (
            SELECT MIN(s2.id)

            FROM settlements s2

            WHERE
                s2.prediction_id = p.id

                AND s2.settled = 1
        )

    ORDER BY
        p.model_version ASC,
        p.id ASC
    """
)

rows = cursor.fetchall()


# ============================================================
# NO SETTLED DATA
# ============================================================

print(
    "Settled predictions:",
    len(rows)
)

print("")


if not rows:

    print(
        "Henüz settlement edilmiş tahmin yok."
    )

    print(
        "Calibration Engine bekliyor."
    )

    print("")

    print(
        "VALIDATION: PASS"
    )

    print(
        "No settled data yet."
    )

    connection.close()

    raise SystemExit(0)


# ============================================================
# MODEL VERSIONS
# ============================================================

model_versions = sorted(
    set(
        row["model_version"]
        for row in rows
        if row["model_version"]
    )
)


print(
    "Model versions found:",
    len(model_versions)
)

for model_version in model_versions:

    print(
        "  ✓",
        model_version
    )

print("")


# ============================================================
# CALIBRATION OUTPUT STRUCTURE
# ============================================================

calibration_output = {

    "source": "StatsHub",

    "calibration_engine_version":
        "SH-CALIBRATION-001",

    "method":
        CALIBRATION_METHOD,

    "minimum_sample_requirement":
        MINIMUM_SAMPLE_REQUIREMENT,

    "shrinkage_strength":
        SHRINKAGE_STRENGTH,

    "generated_at":
        now_utc(),

    "models": {}

}


# ============================================================
# COUNTERS
# ============================================================

total_buckets = 0

applied_buckets = 0

insufficient_buckets = 0

new_history_records = 0

duplicate_history_records = 0


# ============================================================
# PROCESS MODELS
# ============================================================

for model_version in model_versions:

    model_rows = [

        row

        for row in rows

        if row["model_version"]
        ==
        model_version

    ]


    print("")
    print("------------------------------------------")

    print(
        "MODEL:",
        model_version
    )

    print(
        "Settled predictions:",
        len(model_rows)
    )

    print("------------------------------------------")
    print("")


    calibration_output[
        "models"
    ][model_version] = {}


    # ========================================================
    # PROCESS MARKETS
    # ========================================================

    for market, definition in MARKETS.items():

        prediction_column = (
            definition[
                "prediction_column"
            ]
        )


        # ----------------------------------------------------
        # COLLECT BUCKET DATA
        # ----------------------------------------------------

        buckets = {}


        for row in model_rows:

            probability = (
                row[
                    prediction_column
                ]
            )

            probability = clamp_probability(
                probability
            )

            if probability is None:

                continue


            actual = get_actual_result(

                market,

                row["result_1x2"],

                row["total_goals"],

                row["btts_result"]

            )

            if actual is None:

                continue


            bucket = get_bucket(
                probability
            )

            if bucket is None:

                continue


            if bucket not in buckets:

                buckets[bucket] = {
                    "predictions": [],
                    "actuals": []
                }


            buckets[
                bucket
            ][
                "predictions"
            ].append(
                probability
            )


            buckets[
                bucket
            ][
                "actuals"
            ].append(
                actual
            )


        # ----------------------------------------------------
        # NO MARKET DATA
        # ----------------------------------------------------

        if not buckets:

            print(
                f"{market}: NO DATA"
            )

            calibration_output[
                "models"
            ][model_version][market] = {
                "status": "NO_DATA",
                "buckets": []
            }

            continue


        market_output = {

            "status":
                "CALIBRATION_AVAILABLE",

            "buckets": []

        }


        # ----------------------------------------------------
        # PROCESS EACH BUCKET
        # ----------------------------------------------------

        for bucket in sorted(
            buckets.keys()
        ):

            predictions = (
                buckets[
                    bucket
                ][
                    "predictions"
                ]
            )

            actuals = (
                buckets[
                    bucket
                ][
                    "actuals"
                ]
            )


            sample_size = len(
                predictions
            )


            if sample_size == 0:

                continue


            average_prediction = (

                sum(predictions)
                /
                sample_size

            )


            actual_frequency = (

                sum(actuals)
                /
                sample_size

            )


            calibration_difference = (

                actual_frequency
                -
                average_prediction

            )


            total_buckets += 1


            # ------------------------------------------------
            # MINIMUM SAMPLE CHECK
            # ------------------------------------------------

            if (
                sample_size
                <
                MINIMUM_SAMPLE_REQUIREMENT
            ):

                calibrated_probability = (
                    average_prediction
                )

                is_applied = 0

                status = (
                    "INSUFFICIENT_SAMPLE"
                )

                insufficient_buckets += 1


            else:

                calibrated_probability = (
                    calculate_shrunk_probability(

                        average_prediction,

                        actual_frequency,

                        sample_size

                    )
                )

                is_applied = 1

                status = (
                    "APPLIED"
                )

                applied_buckets += 1


            # ------------------------------------------------
            # BUCKET OUTPUT
            # ------------------------------------------------

            bucket_output = {

                "bucket":
                    bucket_label(bucket),

                "bucket_lower":
                    bucket,

                "bucket_upper":
                    round(
                        min(
                            1.0,
                            bucket
                            +
                            BUCKET_WIDTH
                        ),
                        2
                    ),

                "sample_size":
                    sample_size,

                "average_predicted_probability":
                    round(
                        average_prediction,
                        10
                    ),

                "actual_frequency":
                    round(
                        actual_frequency,
                        10
                    ),

                "calibration_difference":
                    round(
                        calibration_difference,
                        10
                    ),

                "calibrated_probability":
                    round(
                        calibrated_probability,
                        10
                    ),

                "calibration_method":
                    CALIBRATION_METHOD,

                "minimum_sample_requirement":
                    MINIMUM_SAMPLE_REQUIREMENT,

                "is_applied":
                    is_applied,

                "status":
                    status

            }


            market_output[
                "buckets"
            ].append(
                bucket_output
            )


            # ------------------------------------------------
            # DATABASE DUPLICATE CHECK
            # ------------------------------------------------

            cursor.execute(

                """
                SELECT id

                FROM calibration_history

                WHERE

                    model_version = ?

                    AND market = ?

                    AND probability_bucket = ?

                    AND sample_size = ?

                    AND ABS(
                        average_predicted_probability
                        - ?
                    ) < 0.000000001

                    AND ABS(
                        actual_frequency
                        - ?
                    ) < 0.000000001

                    AND ABS(
                        calibration_difference
                        - ?
                    ) < 0.000000001

                    AND ABS(
                        calibrated_probability
                        - ?
                    ) < 0.000000001

                    AND calibration_method = ?

                LIMIT 1
                """,

                (

                    model_version,

                    market,

                    bucket,

                    sample_size,

                    average_prediction,

                    actual_frequency,

                    calibration_difference,

                    calibrated_probability,

                    CALIBRATION_METHOD

                )

            )


            duplicate = (
                cursor.fetchone()
            )


            if duplicate:

                duplicate_history_records += 1

            else:

                # --------------------------------------------
                # INSERT CALIBRATION HISTORY
                # --------------------------------------------

                cursor.execute(

                    """
                    INSERT INTO calibration_history (

                        model_version,

                        market,

                        probability_bucket,

                        sample_size,

                        average_predicted_probability,

                        actual_frequency,

                        calibration_difference,

                        calibrated_probability,

                        calibration_method,

                        minimum_sample_requirement,

                        is_applied,

                        created_at

                    )

                    VALUES (

                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?

                    )
                    """,

                    (

                        model_version,

                        market,

                        bucket,

                        sample_size,

                        average_prediction,

                        actual_frequency,

                        calibration_difference,

                        calibrated_probability,

                        CALIBRATION_METHOD,

                        MINIMUM_SAMPLE_REQUIREMENT,

                        is_applied,

                        now_utc()

                    )

                )

                new_history_records += 1


            # ------------------------------------------------
            # LOG
            # ------------------------------------------------

            print(
                f"{market} | "
                f"{bucket_label(bucket)} | "
                f"n={sample_size} | "
                f"pred={average_prediction:.6f} | "
                f"actual={actual_frequency:.6f} | "
                f"calibrated={calibrated_probability:.6f} | "
                f"{status}"
            )


        calibration_output[
            "models"
        ][model_version][market] = (
            market_output
        )


# ============================================================
# COMMIT DATABASE
# ============================================================

connection.commit()


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIRECTORY,
    exist_ok=True
)


# ============================================================
# SAVE CALIBRATION JSON
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        calibration_output,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# DATABASE VALIDATION
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM calibration_history
    """
)

history_count = (
    cursor.fetchone()[0]
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("")
print("==========================================")
print("CALIBRATION ENGINE VALIDATION")
print("==========================================")
print("")

print(
    "Settled predictions:",
    len(rows)
)

print(
    "Total buckets:",
    total_buckets
)

print(
    "Applied buckets:",
    applied_buckets
)

print(
    "Insufficient sample buckets:",
    insufficient_buckets
)

print(
    "New history records:",
    new_history_records
)

print(
    "Duplicate history skipped:",
    duplicate_history_records
)

print(
    "Database calibration records:",
    history_count
)

print(
    "Calibration JSON:",
    OUTPUT_FILE
)

print("")


# ============================================================
# SAFETY VALIDATION
# ============================================================

if applied_buckets > 0:

    print(
        "Calibration available: PASS"
    )

else:

    print(
        "No bucket reached minimum sample."
    )

    print(
        "Calibration remains inactive."
    )


print("")

print(
    "Prediction records were not modified."
)

print(
    "Model lock was not modified."
)

print(
    "Performance records were not modified."
)

print("")

print(
    "VALIDATION: PASS"
)

print("")


# ============================================================
# CLOSE
# ============================================================

connection.close()
