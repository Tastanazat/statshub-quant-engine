import json
import os
import sqlite3
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# RECORD MODEL PREDICTION
# ============================================================

MODEL_FILE = "data/statshub_match_model.json"

DATABASE_FILE = os.path.join(
    "data",
    "database",
    "quant_engine.db"
)

# Current StatsHub fixture
FIXTURE_ID = "416477"

# Current fixture status
# This value is only used when creating the match record.
MATCH_STATUS = "notstarted"


# ============================================================
# FILE CHECKS
# ============================================================

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        f"Model dosyası bulunamadı: {MODEL_FILE}"
    )


if not os.path.exists(DATABASE_FILE):
    raise FileNotFoundError(
        f"Database bulunamadı: {DATABASE_FILE}"
    )


# ============================================================
# LOAD MODEL
# ============================================================

with open(
    MODEL_FILE,
    "r",
    encoding="utf-8"
) as f:

    model = json.load(f)


# ============================================================
# MODEL VALIDATION
# ============================================================

if model.get("source") != "StatsHub":

    raise ValueError(
        "Model kaynağı StatsHub değil."
    )


model_version = model.get(
    "model_version"
)

if not model_version:

    raise ValueError(
        "Model version bulunamadı."
    )


fixture = model.get(
    "fixture",
    {}
)

home_team = fixture.get(
    "home"
)

away_team = fixture.get(
    "away"
)

if not home_team:
    raise ValueError(
        "Home takım bulunamadı."
    )

if not away_team:
    raise ValueError(
        "Away takım bulunamadı."
    )


probabilities = model.get(
    "probabilities",
    {}
)

lambdas = model.get(
    "lambda",
    {}
)


# ============================================================
# REQUIRED PROBABILITIES
# ============================================================

required_probabilities = [

    "home_win",
    "draw",
    "away_win",

    "over_0_5",
    "under_0_5",

    "over_1_5",
    "under_1_5",

    "over_2_5",
    "under_2_5",

    "over_3_5",
    "under_3_5",

    "over_4_5",
    "under_4_5",

    "btts_yes",
    "btts_no"
]


for key in required_probabilities:

    if key not in probabilities:

        raise ValueError(
            f"Eksik probability alanı: {key}"
        )


# ============================================================
# REQUIRED LAMBDAS
# ============================================================

home_lambda = lambdas.get(
    "home"
)

away_lambda = lambdas.get(
    "away"
)


if home_lambda is None:

    raise ValueError(
        "Home lambda bulunamadı."
    )


if away_lambda is None:

    raise ValueError(
        "Away lambda bulunamadı."
    )


# ============================================================
# VALIDATION
# ============================================================

validation = model.get(
    "validation",
    {}
)

if not validation.get(
    "validation_passed",
    False
):

    raise ValueError(
        "Model matematiksel validation PASS değil."
    )


# ============================================================
# CONNECT DATABASE
# ============================================================

connection = sqlite3.connect(
    DATABASE_FILE
)

cursor = connection.cursor()


cursor.execute(
    "PRAGMA foreign_keys = ON"
)


# ============================================================
# TIMESTAMP
# ============================================================

now = datetime.now(
    timezone.utc
).isoformat()


# ============================================================
# MATCH RECORD
# ============================================================

cursor.execute(
    """
    SELECT id
    FROM matches
    WHERE statshub_fixture_id = ?
    """,
    (FIXTURE_ID,)
)

match_row = cursor.fetchone()


if match_row:

    match_id = match_row[0]

    cursor.execute(
        """
        UPDATE matches

        SET
            home_team = ?,
            away_team = ?,
            status = ?,
            updated_at = ?

        WHERE id = ?
        """,
        (
            home_team,
            away_team,
            MATCH_STATUS,
            now,
            match_id
        )
    )

else:

    cursor.execute(
        """
        INSERT INTO matches (

            statshub_fixture_id,
            home_team,
            away_team,
            match_date,
            status,
            final_home_score,
            final_away_score,
            created_at,
            updated_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE_ID,
            home_team,
            away_team,
            None,
            MATCH_STATUS,
            None,
            None,
            now,
            now
        )
    )

    match_id = cursor.lastrowid


# ============================================================
# DUPLICATE PROTECTION
# ============================================================

cursor.execute(
    """
    SELECT id
    FROM predictions

    WHERE
        match_id = ?
        AND model_version = ?
    """,
    (
        match_id,
        model_version
    )
)

existing_prediction = cursor.fetchone()


if existing_prediction:

    connection.commit()
    connection.close()

    print("")
    print("==========================================")
    print("STATSHUB QUANT ENGINE")
    print("==========================================")
    print("")
    print("Prediction zaten kayıtlı.")
    print("")
    print("Match ID:", match_id)
    print("Fixture ID:", FIXTURE_ID)
    print("Model:", model_version)
    print("Prediction ID:", existing_prediction[0])
    print("")
    print("Yeni duplicate prediction oluşturulmadı.")
    print("")
    raise SystemExit(0)


# ============================================================
# MONTE CARLO
# ============================================================

# Current model is deterministic Poisson.
# Monte Carlo will be added as a separate validated layer.

monte_carlo_simulations = 0


# ============================================================
# INSERT PREDICTION
# ============================================================

cursor.execute(
    """
    INSERT INTO predictions (

        match_id,

        model_version,

        prediction_time,

        model_locked,

        home_win_probability,
        draw_probability,
        away_win_probability,

        over_0_5_probability,
        under_0_5_probability,

        over_1_5_probability,
        under_1_5_probability,

        over_2_5_probability,
        under_2_5_probability,

        over_3_5_probability,
        under_3_5_probability,

        over_4_5_probability,
        under_4_5_probability,

        btts_yes_probability,
        btts_no_probability,

        home_lambda,
        away_lambda,

        monte_carlo_simulations,

        created_at

    )

    VALUES (

        ?, ?, ?, ?,

        ?, ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?, ?,

        ?,

        ?
    )
    """,
    (

        match_id,

        model_version,

        now,

        1,

        probabilities["home_win"],
        probabilities["draw"],
        probabilities["away_win"],

        probabilities["over_0_5"],
        probabilities["under_0_5"],

        probabilities["over_1_5"],
        probabilities["under_1_5"],

        probabilities["over_2_5"],
        probabilities["under_2_5"],

        probabilities["over_3_5"],
        probabilities["under_3_5"],

        probabilities["over_4_5"],
        probabilities["under_4_5"],

        probabilities["btts_yes"],
        probabilities["btts_no"],

        home_lambda,
        away_lambda,

        monte_carlo_simulations,

        now
    )
)


prediction_id = cursor.lastrowid


# ============================================================
# COMMIT
# ============================================================

connection.commit()


# ============================================================
# VALIDATION
# ============================================================

cursor.execute(
    """
    SELECT
        id,
        match_id,
        model_version,
        model_locked
    FROM predictions
    WHERE id = ?
    """,
    (prediction_id,)
)

saved_prediction = cursor.fetchone()


if saved_prediction is None:

    connection.close()

    raise RuntimeError(
        "Prediction database'e kaydedilemedi."
    )


connection.close()


# ============================================================
# RESULT
# ============================================================

print("")
print("==========================================")
print("STATSHUB QUANT ENGINE")
print("PREDICTION RECORDED")
print("==========================================")
print("")

print(
    "Prediction ID:",
    prediction_id
)

print(
    "Match ID:",
    match_id
)

print(
    "StatsHub Fixture ID:",
    FIXTURE_ID
)

print(
    "Match:",
    home_team,
    "vs",
    away_team
)

print(
    "Model:",
    model_version
)

print(
    "Model Locked:",
    "YES"
)

print("")

print(
    "Home Win:",
    probabilities["home_win"]
)

print(
    "Draw:",
    probabilities["draw"]
)

print(
    "Away Win:",
    probabilities["away_win"]
)

print("")

print(
    "Over 2.5:",
    probabilities["over_2_5"]
)

print(
    "Under 2.5:",
    probabilities["under_2_5"]
)

print(
    "BTTS Yes:",
    probabilities["btts_yes"]
)

print(
    "BTTS No:",
    probabilities["btts_no"]
)

print("")

print(
    "Home Lambda:",
    home_lambda
)

print(
    "Away Lambda:",
    away_lambda
)

print("")

print(
    "VALIDATION: PASS"
)

print(
    "Prediction database'e kaydedildi."
)

print("")
