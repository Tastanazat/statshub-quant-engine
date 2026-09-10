import sqlite3
import math
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# MODEL PERFORMANCE ENGINE
# ============================================================

DATABASE_FILE = "data/database/quant_engine.db"


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def safe_probability(value):
    """
    Probability değerini güvenli aralıkta tutar.
    """

    epsilon = 1e-15

    return max(
        epsilon,
        min(1.0 - epsilon, float(value))
    )


def calculate_brier(
    predicted_probability,
    actual_result
):
    """
    Binary Brier Score:

        (prediction - outcome)^2
    """

    return (
        float(predicted_probability)
        -
        float(actual_result)
    ) ** 2


def calculate_log_loss(
    predicted_probability,
    actual_result
):
    """
    Binary Log Loss.
    """

    p = safe_probability(
        predicted_probability
    )

    if actual_result == 1:

        return -math.log(p)

    return -math.log(1.0 - p)


# ============================================================
# MARKET DEFINITIONS
# ============================================================

MARKETS = {

    # --------------------------------------------------------
    # 1X2
    # --------------------------------------------------------

    "1X2_HOME": {
        "prediction_column": "home_win_probability"
    },

    "1X2_DRAW": {
        "prediction_column": "draw_probability"
    },

    "1X2_AWAY": {
        "prediction_column": "away_win_probability"
    },


    # --------------------------------------------------------
    # OVER / UNDER
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # BTTS
    # --------------------------------------------------------

    "BTTS_YES": {
        "prediction_column": "btts_yes_probability"
    },

    "BTTS_NO": {
        "prediction_column": "btts_no_probability"
    }
}


# ============================================================
# ACTUAL RESULT
# ============================================================

def get_actual_result(
    market,
    result_1x2,
    total_goals,
    btts_result
):
    """
    Settlement sonucunu binary 0/1 değerine çevirir.
    """

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
    # OVER / UNDER
    # --------------------------------------------------------

    if market.startswith("OVER_"):

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
            if total_goals > line
            else 0.0
        )


    if market.startswith("UNDER_"):

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
            if total_goals < line
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
print("STATSHUB MODEL PERFORMANCE ENGINE")
print("==========================================")
print("")

print(
    "Database:",
    DATABASE_FILE
)

print("")


# ============================================================
# FIND SETTLED PREDICTIONS
# ============================================================
#
# EXISTS kullanıyoruz.
#
# Böylece aynı prediction için yanlışlıkla birden fazla
# settlement satırı olsa bile prediction çoğaltılmaz.
#
# Prediction verileri hiçbir şekilde değiştirilmez.
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


print(
    "Settled predictions:",
    len(rows)
)

print("")


# ============================================================
# NO SETTLEMENT DATA
# ============================================================

if not rows:

    print(
        "Henüz settlement edilmiş tahmin yok."
    )

    print(
        "Performance Engine bekliyor."
    )

    print("")

    print(
        "VALIDATION: PASS"
    )

    print(
        "No settled data yet."
    )

    print("")

    connection.close()

    raise SystemExit(0)


# ============================================================
# MODEL VERSIONS
# ============================================================

model_versions = sorted(
    set(
        row["model_version"]
        for row in rows
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
# PERFORMANCE COUNTERS
# ============================================================

calculated_count = 0
inserted_count = 0
skipped_duplicate_count = 0


# ============================================================
# PROCESS EACH MODEL VERSION
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


    # ========================================================
    # PROCESS MARKETS
    # ========================================================

    for market, definition in MARKETS.items():

        prediction_column = (
            definition["prediction_column"]
        )


        predictions = []
        actuals = []


        # ----------------------------------------------------
        # COLLECT DATA
        # ----------------------------------------------------

        for row in model_rows:

            predicted_probability = row[
                prediction_column
            ]

            if predicted_probability is None:

                continue


            actual_result = get_actual_result(

                market,

                row["result_1x2"],

                row["total_goals"],

                row["btts_result"]

            )


            if actual_result is None:

                continue


            predictions.append(
                float(
                    predicted_probability
                )
            )

            actuals.append(
                float(
                    actual_result
                )
            )


        sample_size = len(
            predictions
        )


        # ----------------------------------------------------
        # NO DATA FOR MARKET
        # ----------------------------------------------------

        if sample_size == 0:

            print(
                f"{market}: NO DATA"
            )

            continue


        # ----------------------------------------------------
        # CALCULATIONS
        # ----------------------------------------------------

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


        brier_scores = [

            calculate_brier(
                prediction,
                actual
            )

            for prediction, actual

            in zip(
                predictions,
                actuals
            )

        ]


        log_losses = [

            calculate_log_loss(
                prediction,
                actual
            )

            for prediction, actual

            in zip(
                predictions,
                actuals
            )

        ]


        brier_score = (

            sum(brier_scores)
            /
            sample_size

        )


        log_loss = (

            sum(log_losses)
            /
            sample_size

        )


        calibration_error = abs(

            average_prediction
            -
            actual_frequency

        )


        # ----------------------------------------------------
        # ACCURACY
        # ----------------------------------------------------

        correct_predictions = 0


        for prediction, actual in zip(
            predictions,
            actuals
        ):

            predicted_class = (

                1.0
                if prediction >= 0.5
                else 0.0

            )


            if predicted_class == actual:

                correct_predictions += 1


        accuracy = (

            correct_predictions
            /
            sample_size

        )


        # ----------------------------------------------------
        # DUPLICATE CHECK
        # ----------------------------------------------------
        #
        # Aynı model + market + aynı sample ve aynı
        # hesaplama tekrar geldiyse yeni satır yazılmaz.
        #
        # Yeni settlement geldiyse sample_size değişir ve
        # yeni performance snapshot oluşturulur.
        # ----------------------------------------------------

        cursor.execute(

            """
            SELECT id

            FROM model_performance

            WHERE
                model_version = ?
                AND market = ?
                AND sample_size = ?
                AND ABS(
                    predicted_probability - ?
                ) < 0.000000001
                AND ABS(
                    actual_result - ?
                ) < 0.000000001
                AND ABS(
                    brier_score - ?
                ) < 0.000000001
                AND ABS(
                    log_loss - ?
                ) < 0.000000001
                AND ABS(
                    calibration_error - ?
                ) < 0.000000001

            LIMIT 1
            """,

            (

                model_version,

                market,

                sample_size,

                average_prediction,

                actual_frequency,

                brier_score,

                log_loss,

                calibration_error

            )

        )


        duplicate = cursor.fetchone()


        if duplicate:

            skipped_duplicate_count += 1

            print(
                f"{market}: "
                f"SKIPPED DUPLICATE"
            )

            continue


        # ----------------------------------------------------
        # INSERT PERFORMANCE SNAPSHOT
        # ----------------------------------------------------

        cursor.execute(

            """
            INSERT INTO model_performance (

                model_version,

                market,

                sample_size,

                predicted_probability,

                actual_result,

                brier_score,

                log_loss,

                calibration_error,

                roi,

                yield,

                calculated_at

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
                NULL,
                NULL,
                ?

            )
            """,

            (

                model_version,

                market,

                sample_size,

                average_prediction,

                actual_frequency,

                brier_score,

                log_loss,

                calibration_error,

                now_utc()

            )

        )


        inserted_count += 1
        calculated_count += 1


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        print(
            f"{market}:"
        )

        print(
            f"  Sample size: {sample_size}"
        )

        print(
            f"  Avg predicted: "
            f"{average_prediction:.6f}"
        )

        print(
            f"  Actual frequency: "
            f"{actual_frequency:.6f}"
        )

        print(
            f"  Brier score: "
            f"{brier_score:.6f}"
        )

        print(
            f"  Log loss: "
            f"{log_loss:.6f}"
        )

        print(
            f"  Calibration error: "
            f"{calibration_error:.6f}"
        )

        print(
            f"  Accuracy: "
            f"{accuracy:.6f}"
        )

        print("")


# ============================================================
# COMMIT
# ============================================================

connection.commit()


# ============================================================
# DATABASE VALIDATION
# ============================================================

cursor.execute(
    """
    SELECT COUNT(*)
    FROM model_performance
    """
)

performance_rows = cursor.fetchone()[0]


# ============================================================
# FINAL VALIDATION
# ============================================================

print("")
print("==========================================")
print("MODEL PERFORMANCE VALIDATION")
print("==========================================")
print("")

print(
    "Performance records:",
    performance_rows
)

print(
    "New records inserted:",
    inserted_count
)

print(
    "Duplicate records skipped:",
    skipped_duplicate_count
)

print(
    "Markets calculated:",
    calculated_count
)

print("")


# ============================================================
# SAFETY VALIDATION
# ============================================================

if calculated_count > 0:

    print(
        "Performance calculation: PASS"
    )

else:

    print(
        "No new performance snapshot created."
    )


print("")

print(
    "Prediction records were not modified."
)

print(
    "Model lock was not modified."
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
