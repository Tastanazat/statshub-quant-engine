import sqlite3
import json
import os
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# MODEL CALIBRATION ENGINE V2
# ============================================================

DATABASE_FILE = "data/database/quant_engine.db"

OUTPUT_DIRECTORY = "data/models"

OUTPUT_FILE = "data/models/calibration.json"


# ============================================================
# CALIBRATION SETTINGS
# ============================================================

CALIBRATION_METHOD = "EMPIRICAL_BUCKET_SHRINKAGE"

MINIMUM_SAMPLE_REQUIREMENT = 30

BUCKET_WIDTH = 0.10

SHRINKAGE_STRENGTH = 30.0


# ============================================================
# MARKET DEFINITIONS
# ============================================================

MARKETS = {

    "1X2_HOME": {
        "prediction_column": "home_win_probability"
    },

    "1X2_DRAW": {
        "prediction_column": "draw_probability"
    },

    "1X2_AWAY": {
        "prediction_column": "away_win_probability"
    },

    "OVER_0_5": {
        "prediction_column": "over_0_5_probability"
    },

    "UNDER_0_5": {
        "prediction_column": "under_0_5_probability"
    },

    "OVER_1_5": {
        "prediction_column": "over_1_5_probability"
    },

    "UNDER_1_5": {
        "prediction_column": "under_1_5_probability"
    },

    "OVER_2_5": {
        "prediction_column": "over_2_5_probability"
    },

    "UNDER_2_5": {
        "prediction_column": "under_2_5_probability"
    },

    "OVER_3_5": {
        "prediction_column": "over_3_5_probability"
    },

    "UNDER_3_5": {
        "prediction_column": "under_3_5_probability"
    },

    "OVER_4_5": {
        "prediction_column": "over_4_5_probability"
    },

    "UNDER_4_5": {
        "prediction_column": "under_4_5_probability"
    },

    "BTTS_YES": {
        "prediction_column": "btts_yes_probability"
    },

    "BTTS_NO": {
        "prediction_column": "btts_no_probability"
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
    except (TypeError, ValueError):
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
# NORMALIZE RESULT
# ============================================================

def normalize_result(value):

    if value is None:
        return None

    value = str(value).strip().upper()

    replacements = {
        "HOME_WIN": "HOME",
        "HOME": "HOME",

        "DRAW": "DRAW",
        "X": "DRAW",

        "AWAY_WIN": "AWAY",
        "AWAY": "AWAY",

        "YES": "YES",
        "NO": "NO"
    }

    return replacements.get(
        value,
        value
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

    result_1x2 = normalize_result(
        result_1x2
    )

    btts_result = normalize_result(
        btts_result
    )

    # --------------------------------------------------------
    # 1X2 HOME
    # --------------------------------------------------------

    if market == "1X2_HOME":

        if result_1x2 not in (
            "HOME",
            "DRAW",
            "AWAY"
        ):
            return None

        return 1.0 if result_1x2 == "HOME" else 0.0


    # --------------------------------------------------------
    # 1X2 DRAW
    # --------------------------------------------------------

    if market == "1X2_DRAW":

        if result_1x2 not in (
            "HOME",
            "DRAW",
            "AWAY"
        ):
            return None

        return 1.0 if result_1x2 == "DRAW" else 0.0


    # --------------------------------------------------------
    # 1X2 AWAY
    # --------------------------------------------------------

    if market == "1X2_AWAY":

        if result_1x2 not in (
            "HOME",
            "DRAW",
            "AWAY"
        ):
            return None

        return 1.0 if result_1x2 == "AWAY" else 0.0


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

        try:
            line = float(
                line_text.replace(
                    "_",
                    "."
                )
            )
        except ValueError:
            return None

        goals = safe_float(
            total_goals
        )

        if goals is None:
            return None

        return 1.0 if goals > line else 0.0


    # --------------------------------------------------------
    # UNDER
    # --------------------------------------------------------

    if market.startswith("UNDER_"):

        if total_goals is None:
            return None

        line_text = market.replace(
            "UNDER_",
            ""
        )

        try:
            line = float(
                line_text.replace(
                    "_",
                    "."
                )
            )
        except ValueError:
            return None

        goals = safe_float(
            total_goals
        )

        if goals is None:
            return None

        return 1.0 if goals < line else 0.0


    # --------------------------------------------------------
    # BTTS YES
    # --------------------------------------------------------

    if market == "BTTS_YES":

        if btts_result not in (
            "YES",
            "NO"
        ):
            return None

        return 1.0 if btts_result == "YES" else 0.0


    # --------------------------------------------------------
    # BTTS NO
    # --------------------------------------------------------

    if market == "BTTS_NO":

        if btts_result not in (
            "YES",
            "NO"
        ):
            return None

        return 1.0 if btts_result == "NO" else 0.0


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

    # 100% -> 90-100%
    if probability >= 1.0:
        return 0.90

    bucket = (
        int(
            probability /
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
            0.90,
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

    upper = min(
        100,
        lower + 10
    )

    return f"{lower:02d}-{upper:02d}%"


# ============================================================
# SHRINKED CALIBRATION
# ============================================================

def calculate_shrunk_probability(
    average_prediction,
    actual_frequency,
    sample_size
):

    n = float(
        sample_size
    )

    strength = float(
        SHRINKAGE_STRENGTH
    )

    weight_actual = (
        n /
        (
            n + strength
        )
    )

    weight_prediction = (
        strength /
        (
            n + strength
        )
    )

    calibrated = (

        weight_prediction
        *
        average_prediction

        +

        weight_actual
        *
        actual_frequency
    )

    return max(
        0.0,
        min(
            1.0,
            calibrated
        )
    )


# ============================================================
# EMPTY OUTPUT
# ============================================================

def create_empty_calibration_output():

    return {

        "source": "StatsHub",

        "calibration_engine_version":
            "SH-CALIBRATION-002",

        "method":
            CALIBRATION_METHOD,

        "minimum_sample_requirement":
            MINIMUM_SAMPLE_REQUIREMENT,

        "bucket_width":
            BUCKET_WIDTH,

        "shrinkage_strength":
            SHRINKAGE_STRENGTH,

        "generated_at":
            now_utc(),

        "status":
            "WAITING_FOR_SETTLEMENT",

        "settled_predictions":
            0,

        "models":
            {}
    }


# ============================================================
# SAVE JSON
# ============================================================

def save_calibration_json(
    calibration_output
):

    os.makedirs(
        OUTPUT_DIRECTORY,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            calibration_output,
            file,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# HEADER
# ============================================================

print("")
print("==========================================")
print("STATSHUB MODEL CALIBRATION ENGINE V2")
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
    "Bucket width:",
    BUCKET_WIDTH
)

print(
    "Shrinkage strength:",
    SHRINKAGE_STRENGTH
)

print("")


# ============================================================
# DATABASE EXISTS
# ============================================================

if not os.path.exists(
    DATABASE_FILE
):

    raise SystemExit(
        "ERROR: Database bulunamadı: "
        + DATABASE_FILE
    )


# ============================================================
# CONNECT
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
# CHECK REQUIRED TABLES
# ============================================================

required_tables = [
    "predictions",
    "settlements",
    "calibration_history"
]

for table_name in required_tables:

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """,
        (table_name,)
    )

    if cursor.fetchone() is None:

        connection.close()

        raise SystemExit(
            "ERROR: Gerekli tablo bulunamadı: "
            + table_name
        )


print(
    "Database tables: PASS"
)

print("")


# ============================================================
# FIND SETTLED PREDICTIONS
# ============================================================

query = """

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


try:

    cursor.execute(
        query
    )

    rows = cursor.fetchall()

except sqlite3.Error as error:

    connection.close()

    raise SystemExit(
        "ERROR: Settled prediction sorgusu başarısız: "
        + str(error)
    )


# ============================================================
# SETTLEMENT COUNT
# ============================================================

print(
    "Settled predictions:",
    len(rows)
)

print("")


# ============================================================
# NO SETTLED DATA
# ============================================================

if not rows:

    calibration_output = (
        create_empty_calibration_output()
    )

    save_calibration_json(
        calibration_output
    )

    print(
        "Henüz settlement edilmiş tahmin yok."
    )

    print(
        "Calibration Engine bekliyor."
    )

    print(
        "Calibration JSON oluşturuldu:"
    )

    print(
        OUTPUT_FILE
    )

    print("")
    print(
        "Prediction records modified: NO"
    )

    print(
        "Model lock modified: NO"
    )

    print("")
    print(
        "VALIDATION: PASS"
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
        if row["model_version"] is not None
        and str(row["model_version"]).strip() != ""
    )
)


print(
    "Model versions found:",
    len(model_versions)
)

for version in model_versions:

    print(
        "  ✓",
        version
    )

print("")


# ============================================================
# OUTPUT STRUCTURE
# ============================================================

calibration_output = {

    "source":
        "StatsHub",

    "calibration_engine_version":
        "SH-CALIBRATION-002",

    "method":
        CALIBRATION_METHOD,

    "minimum_sample_requirement":
        MINIMUM_SAMPLE_REQUIREMENT,

    "bucket_width":
        BUCKET_WIDTH,

    "shrinkage_strength":
        SHRINKAGE_STRENGTH,

    "generated_at":
        now_utc(),

    "status":
        "CALIBRATION_AVAILABLE",

    "settled_predictions":
        len(rows),

    "models":
        {}
}


# ============================================================
# COUNTERS
# ============================================================

total_buckets = 0

applied_buckets = 0

insufficient_buckets = 0

new_history_records = 0

duplicate_history_records = 0

valid_market_records = 0


# ============================================================
# PROCESS EACH MODEL
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


        buckets = {}


        # ====================================================
        # COLLECT DATA
        # ====================================================

        for row in model_rows:

            probability = clamp_probability(
                row[
                    prediction_column
                ]
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


            valid_market_records += 1


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


        # ====================================================
        # NO DATA
        # ====================================================

        if not buckets:

            print(
                f"{market}: NO DATA"
            )

            calibration_output[
                "models"
            ][model_version][market] = {

                "status":
                    "NO_DATA",

                "buckets":
                    []
            }

            continue


        market_output = {

            "status":
                "CALIBRATION_AVAILABLE",

            "buckets":
                []
        }


        # ====================================================
        # PROCESS BUCKETS
        # ====================================================

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


            if sample_size <= 0:
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


            # =================================================
            # SAMPLE CHECK
            # =================================================

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

                status = "APPLIED"

                applied_buckets += 1


            # =================================================
            # BUCKET OUTPUT
            # =================================================

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


            # =================================================
            # DUPLICATE HISTORY CHECK
            # =================================================

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


            duplicate = cursor.fetchone()


            # =================================================
            # INSERT HISTORY
            # =================================================

            if duplicate:

                duplicate_history_records += 1

            else:

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


            # =================================================
            # LOG
            # =================================================

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
# COMMIT
# ============================================================

try:

    connection.commit()

except sqlite3.Error as error:

    connection.rollback()

    connection.close()

    raise SystemExit(
        "ERROR: Database commit başarısız: "
        + str(error)
    )


# ============================================================
# SAVE JSON
# ============================================================

try:

    save_calibration_json(
        calibration_output
    )

except Exception as error:

    connection.close()

    raise SystemExit(
        "ERROR: calibration.json yazılamadı: "
        + str(error)
    )


# ============================================================
# VERIFY JSON EXISTS
# ============================================================

if not os.path.exists(
    OUTPUT_FILE
):

    connection.close()

    raise SystemExit(
        "ERROR: calibration.json oluşturulamadı."
    )


# ============================================================
# VERIFY JSON
# ============================================================

try:

    with open(
        OUTPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        validation_json = json.load(
            file
        )

except Exception as error:

    connection.close()

    raise SystemExit(
        "ERROR: calibration.json okunamadı: "
        + str(error)
    )


# ============================================================
# JSON VALIDATION
# ============================================================

if validation_json.get(
    "source"
) != "StatsHub":

    connection.close()

    raise SystemExit(
        "ERROR: calibration.json source StatsHub değil."
    )


if (
    "models"
    not in validation_json
):

    connection.close()

    raise SystemExit(
        "ERROR: calibration.json models alanı eksik."
    )


# ============================================================
# DATABASE COUNT
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
    "Valid market records:",
    valid_market_records
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
# CALIBRATION STATUS
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


# ============================================================
# SAFETY VALIDATION
# ============================================================

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

print(
    "Settlement records were not modified."
)

print("")


# ============================================================
# FINAL PASS
# ============================================================

print(
    "VALIDATION: PASS"
)

print("")


# ============================================================
# CLOSE
# ============================================================

connection.close()
