import sqlite3
import os
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# DATABASE INITIALIZATION
# ============================================================

DATABASE_DIR = "data/database"
DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "quant_engine.db"
)


# ============================================================
# DATABASE DIRECTORY
# ============================================================

os.makedirs(
    DATABASE_DIR,
    exist_ok=True
)


# ============================================================
# CONNECT
# ============================================================

connection = sqlite3.connect(
    DATABASE_FILE
)

cursor = connection.cursor()


# ============================================================
# FOREIGN KEYS
# ============================================================

cursor.execute(
    "PRAGMA foreign_keys = ON"
)


# ============================================================
# 1. MATCHES
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS matches (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        statshub_fixture_id TEXT NOT NULL UNIQUE,

        home_team TEXT NOT NULL,

        away_team TEXT NOT NULL,

        match_date TEXT,

        status TEXT,

        final_home_score INTEGER,

        final_away_score INTEGER,

        created_at TEXT NOT NULL,

        updated_at TEXT NOT NULL
    )
    """
)


# ============================================================
# 2. PREDICTIONS
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS predictions (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        match_id INTEGER NOT NULL,

        model_version TEXT NOT NULL,

        prediction_time TEXT NOT NULL,

        model_locked INTEGER NOT NULL DEFAULT 1,

        home_win_probability REAL,

        draw_probability REAL,

        away_win_probability REAL,

        over_0_5_probability REAL,

        under_0_5_probability REAL,

        over_1_5_probability REAL,

        under_1_5_probability REAL,

        over_2_5_probability REAL,

        under_2_5_probability REAL,

        over_3_5_probability REAL,

        under_3_5_probability REAL,

        over_4_5_probability REAL,

        under_4_5_probability REAL,

        btts_yes_probability REAL,

        btts_no_probability REAL,

        home_lambda REAL,

        away_lambda REAL,

        monte_carlo_simulations INTEGER,

        created_at TEXT NOT NULL,

        FOREIGN KEY (match_id)
            REFERENCES matches(id)
            ON DELETE CASCADE
    )
    """
)


# ============================================================
# 3. SETTLEMENTS
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS settlements (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        prediction_id INTEGER NOT NULL,

        settlement_time TEXT NOT NULL,

        final_home_score INTEGER,

        final_away_score INTEGER,

        result_1x2 TEXT,

        total_goals INTEGER,

        btts_result TEXT,

        over_0_5_result TEXT,

        over_1_5_result TEXT,

        over_2_5_result TEXT,

        over_3_5_result TEXT,

        over_4_5_result TEXT,

        settled INTEGER NOT NULL DEFAULT 1,

        FOREIGN KEY (prediction_id)
            REFERENCES predictions(id)
            ON DELETE CASCADE
    )
    """
)


# ============================================================
# 4. MODEL VERSIONS
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS model_versions (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        model_version TEXT NOT NULL UNIQUE,

        model_type TEXT NOT NULL,

        training_sample_size INTEGER,

        training_start_date TEXT,

        training_end_date TEXT,

        calibration_method TEXT,

        model_parameters TEXT,

        brier_score REAL,

        log_loss REAL,

        calibration_error REAL,

        accuracy REAL,

        roi REAL,

        yield REAL,

        max_drawdown REAL,

        is_active INTEGER NOT NULL DEFAULT 0,

        created_at TEXT NOT NULL
    )
    """
)


# ============================================================
# 5. MODEL PERFORMANCE
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS model_performance (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        model_version TEXT NOT NULL,

        market TEXT NOT NULL,

        sample_size INTEGER NOT NULL,

        predicted_probability REAL,

        actual_result REAL,

        brier_score REAL,

        log_loss REAL,

        calibration_error REAL,

        roi REAL,

        yield REAL,

        calculated_at TEXT NOT NULL
    )
    """
)


# ============================================================
# 6. CALIBRATION HISTORY
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS calibration_history (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        model_version TEXT NOT NULL,

        market TEXT NOT NULL,

        probability_bucket TEXT NOT NULL,

        sample_size INTEGER NOT NULL,

        average_predicted_probability REAL,

        actual_frequency REAL,

        calibration_difference REAL,

        calibrated_probability REAL,

        calibration_method TEXT,

        minimum_sample_requirement INTEGER,

        is_applied INTEGER NOT NULL DEFAULT 0,

        created_at TEXT NOT NULL
    )
    """
)


# ============================================================
# INDEXES
# ============================================================

cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_predictions_match
    ON predictions(match_id)
    """
)


cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_predictions_model
    ON predictions(model_version)
    """
)


cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_settlements_prediction
    ON settlements(prediction_id)
    """
)


cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_calibration_market
    ON calibration_history(market)
    """
)


# ============================================================
# DATABASE METADATA
# ============================================================

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS database_metadata (

        key TEXT PRIMARY KEY,

        value TEXT NOT NULL
    )
    """
)


now = datetime.now(
    timezone.utc
).isoformat()


metadata = {

    "database_version": "1.0",

    "database_created_by":
        "StatsHub Quant Engine",

    "data_source":
        "StatsHub",

    "created_at":
        now
}


for key, value in metadata.items():

    cursor.execute(
        """
        INSERT OR REPLACE INTO
        database_metadata
        (key, value)

        VALUES (?, ?)
        """,
        (key, value)
    )


# ============================================================
# COMMIT
# ============================================================

connection.commit()


# ============================================================
# VALIDATION
# ============================================================

cursor.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """
)

tables = [
    row[0]
    for row in cursor.fetchall()
]


required_tables = [

    "matches",
    "predictions",
    "settlements",
    "model_versions",
    "model_performance",
    "calibration_history",
    "database_metadata"
]


missing_tables = [
    table
    for table in required_tables
    if table not in tables
]


connection.close()


# ============================================================
# RESULT
# ============================================================

print("")
print("==========================================")
print("STATSHUB QUANT ENGINE DATABASE")
print("==========================================")
print("")

print(
    "Database:",
    DATABASE_FILE
)

print("")

print("Tables:")

for table in tables:

    print(
        "  ✓",
        table
    )

print("")


if missing_tables:

    print(
        "VALIDATION: FAIL"
    )

    print(
        "Eksik tablolar:",
        missing_tables
    )

    raise SystemExit(1)


print(
    "VALIDATION: PASS"
)

print("")
print(
    "Database başarıyla oluşturuldu."
)
