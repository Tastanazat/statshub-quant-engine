import sqlite3
from datetime import datetime, timezone


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_FILE = "data/database/quant_engine.db"

FIXTURE_ID = "416477"

EXPECTED_HOME_TEAM = "PSV"
EXPECTED_AWAY_TEAM = "Shakhtar"

EXPECTED_HOME_SCORE = 0
EXPECTED_AWAY_SCORE = 0


# =========================================================
# TIME
# =========================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# MAIN
# =========================================================

def main():

    print("")
    print("==========================================")
    print("INVALID SETTLEMENT CLEANUP")
    print("==========================================")
    print("")

    conn = sqlite3.connect(
        DATABASE_FILE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # -----------------------------------------------------
    # FIND EXACT MATCH
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            statshub_fixture_id,
            home_team,
            away_team,
            status,
            final_home_score,
            final_away_score
        FROM matches
        WHERE statshub_fixture_id = ?
        LIMIT 1
        """,
        (FIXTURE_ID,),
    )

    match = cursor.fetchone()

    if match is None:

        conn.close()

        raise SystemExit(
            "CLEANUP ERROR: "
            "Target fixture bulunamadı."
        )

    print("Fixture:", match["statshub_fixture_id"])
    print("Home:", match["home_team"])
    print("Away:", match["away_team"])
    print("Status:", match["status"])
    print(
        "Final score:",
        match["final_home_score"],
        "-",
        match["final_away_score"]
    )

    # -----------------------------------------------------
    # TEAM SAFETY
    # -----------------------------------------------------

    if (
        str(match["home_team"]).lower()
        != EXPECTED_HOME_TEAM.lower()
        or
        str(match["away_team"]).lower()
        != EXPECTED_AWAY_TEAM.lower()
    ):

        conn.close()

        raise SystemExit(
            "CLEANUP SECURITY ERROR: "
            "Takımlar hedef fixture ile eşleşmiyor."
        )

    match_id = match["id"]

    # -----------------------------------------------------
    # FIND SETTLEMENTS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            s.id,
            s.prediction_id,
            s.final_home_score,
            s.final_away_score,
            s.result_1x2,
            s.total_goals,
            s.settled
        FROM settlements s
        JOIN predictions p
          ON p.id = s.prediction_id
        WHERE p.match_id = ?
        ORDER BY s.id ASC
        """,
        (match_id,),
    )

    settlements = cursor.fetchall()

    print("")
    print(
        "Settlement count:",
        len(settlements)
    )

    if not settlements:

        print("")
        print(
            "TEMİZLENECEK SETTLEMENT YOK."
        )
        print("")

        conn.close()

        return

    # -----------------------------------------------------
    # DELETE ONLY INVALID 0-0 SETTLEMENT
    # -----------------------------------------------------

    deleted_count = 0

    for settlement in settlements:

        settlement_id = settlement["id"]

        home_score = settlement[
            "final_home_score"
        ]

        away_score = settlement[
            "final_away_score"
        ]

        print("")
        print(
            "Settlement ID:",
            settlement_id
        )

        print(
            "Prediction ID:",
            settlement["prediction_id"]
        )

        print(
            "Recorded score:",
            home_score,
            "-",
            away_score
        )

        # -------------------------------------------------
        # SAFETY:
        # ONLY DELETE THE KNOWN INVALID 0-0 RECORD
        # -------------------------------------------------

        if (
            home_score == EXPECTED_HOME_SCORE
            and
            away_score == EXPECTED_AWAY_SCORE
        ):

            cursor.execute(
                """
                DELETE FROM settlements
                WHERE id = ?
                """,
                (settlement_id,),
            )

            deleted_count += 1

            print(
                "INVALID 0-0 SETTLEMENT DELETED."
            )

        else:

            print(
                "Settlement skor 0-0 değil."
            )

            print(
                "SKIP — kayıt korunuyor."
            )

    # -----------------------------------------------------
    # IMPORTANT:
    # DO NOT DELETE PREDICTION
    # -----------------------------------------------------

    print("")
    print(
        "Prediction kayıtları silinmedi."
    )

    # -----------------------------------------------------
    # COMMIT
    # -----------------------------------------------------

    conn.commit()

    # -----------------------------------------------------
    # VERIFY
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM settlements s
        JOIN predictions p
          ON p.id = s.prediction_id
        WHERE p.match_id = ?
        """,
        (match_id,),
    )

    remaining_settlements = cursor.fetchone()[0]

    # -----------------------------------------------------
    # VERIFY PREDICTION STILL EXISTS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM predictions
        WHERE match_id = ?
        """,
        (match_id,),
    )

    prediction_count = cursor.fetchone()[0]

    # -----------------------------------------------------
    # VERIFY MATCH STILL EXISTS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM matches
        WHERE id = ?
        """,
        (match_id,),
    )

    match_count = cursor.fetchone()[0]

    conn.close()

    # -----------------------------------------------------
    # FINAL VALIDATION
    # -----------------------------------------------------

    if match_count != 1:

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Match kaydı değişmiş."
        )

    if prediction_count < 1:

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Prediction kaydı bulunamadı."
        )

    print("")
    print("==========================================")
    print("CLEANUP VALIDATION: PASS")
    print("==========================================")
    print("")
    print(
        "Deleted settlements:",
        deleted_count
    )

    print(
        "Remaining settlements:",
        remaining_settlements
    )

    print(
        "Predictions preserved:",
        prediction_count
    )

    print(
        "Match preserved:",
        match_count
    )

    print("")
    print(
        "Prediction probabilities: PRESERVED"
    )

    print(
        "Model lock: PRESERVED"
    )

    print(
        "Database cleanup: COMPLETE"
    )

    print("")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
