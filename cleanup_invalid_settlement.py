import sqlite3
from datetime import datetime, timezone


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_FILE = "data/database/quant_engine.db"

FIXTURE_ID = "416477"

EXPECTED_HOME_TEAM = "PSV"
EXPECTED_AWAY_TEAM = "Shakhtar"

# Önceki hatalı kayıt
INVALID_PREDICTION_ID = 1
INVALID_SETTLEMENT_ID = 1


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
    print("SAFE INVALID SETTLEMENT CLEANUP")
    print("==========================================")
    print("")

    conn = sqlite3.connect(
        DATABASE_FILE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # -----------------------------------------------------
    # 1. EXACT MATCH
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

    # -----------------------------------------------------
    # 2. TEAM SAFETY
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
            "Takımlar eşleşmiyor."
        )

    match_id = match["id"]

    print(
        "Fixture:",
        match["statshub_fixture_id"]
    )

    print(
        "Match:",
        match["home_team"],
        "vs",
        match["away_team"]
    )

    print(
        "Match ID:",
        match_id
    )

    print(
        "Current status:",
        match["status"]
    )

    print(
        "Current score:",
        match["final_home_score"],
        "-",
        match["final_away_score"]
    )

    # -----------------------------------------------------
    # 3. VERIFY PREDICTION
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            match_id,
            model_version,
            model_locked
        FROM predictions
        WHERE id = ?
          AND match_id = ?
        LIMIT 1
        """,
        (
            INVALID_PREDICTION_ID,
            match_id,
        ),
    )

    prediction = cursor.fetchone()

    if prediction is None:

        conn.close()

        raise SystemExit(
            "CLEANUP ERROR: "
            "Beklenen Prediction ID bulunamadı."
        )

    print("")
    print(
        "Prediction ID:",
        prediction["id"]
    )

    print(
        "Model:",
        prediction["model_version"]
    )

    print(
        "Model locked:",
        prediction["model_locked"]
    )

    # -----------------------------------------------------
    # 4. MODEL LOCK SAFETY
    # -----------------------------------------------------

    if int(
        prediction["model_locked"]
    ) != 1:

        conn.close()

        raise SystemExit(
            "CLEANUP SECURITY ERROR: "
            "Prediction model_locked=1 değil."
        )

    # -----------------------------------------------------
    # 5. VERIFY EXACT SETTLEMENT
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            prediction_id,
            final_home_score,
            final_away_score,
            result_1x2,
            total_goals,
            settled
        FROM settlements
        WHERE id = ?
          AND prediction_id = ?
        LIMIT 1
        """,
        (
            INVALID_SETTLEMENT_ID,
            INVALID_PREDICTION_ID,
        ),
    )

    settlement = cursor.fetchone()

    if settlement is None:

        print("")
        print(
            "Temizlenecek eski settlement bulunamadı."
        )

        conn.close()

        return

    print("")
    print(
        "Settlement ID:",
        settlement["id"]
    )

    print(
        "Settlement Prediction ID:",
        settlement["prediction_id"]
    )

    print(
        "Recorded score:",
        settlement["final_home_score"],
        "-",
        settlement["final_away_score"]
    )

    # -----------------------------------------------------
    # 6. EXTRA SAFETY
    # -----------------------------------------------------
    #
    # Sadece önceki hatalı 0-0 kaydı kabul edilir.
    #

    if (
        settlement["final_home_score"] != 0
        or
        settlement["final_away_score"] != 0
    ):

        conn.close()

        raise SystemExit(
            "CLEANUP SECURITY ERROR: "
            "Settlement skoru beklenen eski 0-0 "
            "kaydına uymuyor."
        )

    # -----------------------------------------------------
    # 7. DELETE EXACT SETTLEMENT ONLY
    # -----------------------------------------------------

    cursor.execute(
        """
        DELETE FROM settlements
        WHERE id = ?
          AND prediction_id = ?
        """,
        (
            INVALID_SETTLEMENT_ID,
            INVALID_PREDICTION_ID,
        ),
    )

    deleted_count = cursor.rowcount

    if deleted_count != 1:

        conn.rollback()
        conn.close()

        raise SystemExit(
            "CLEANUP ERROR: "
            "Settlement silinemedi."
        )

    print("")
    print(
        "Eski hatalı settlement silindi."
    )

    # -----------------------------------------------------
    # 8. RESET MATCH RESULT
    # -----------------------------------------------------
    #
    # Maç gerçekte bitmediği için önceki yanlış
    # settlement'ın matches tablosuna yazdığı sonucu
    # temizliyoruz.
    #

    cursor.execute(
        """
        UPDATE matches
        SET
            status = ?,
            final_home_score = NULL,
            final_away_score = NULL,
            updated_at = ?
        WHERE id = ?
          AND statshub_fixture_id = ?
        """,
        (
            "notstarted",
            now_utc(),
            match_id,
            FIXTURE_ID,
        ),
    )

    if cursor.rowcount != 1:

        conn.rollback()
        conn.close()

        raise SystemExit(
            "CLEANUP ERROR: "
            "Match status reset başarısız."
        )

    print(
        "Match status: notstarted"
    )

    print(
        "Final score: NULL - NULL"
    )

    # -----------------------------------------------------
    # 9. COMMIT
    # -----------------------------------------------------

    conn.commit()

    # -----------------------------------------------------
    # 10. VERIFY SETTLEMENT DELETED
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM settlements
        WHERE id = ?
          AND prediction_id = ?
        """,
        (
            INVALID_SETTLEMENT_ID,
            INVALID_PREDICTION_ID,
        ),
    )

    settlement_exists = cursor.fetchone()[0]

    if settlement_exists != 0:

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Settlement hâlâ mevcut."
        )

    # -----------------------------------------------------
    # 11. VERIFY PREDICTION PRESERVED
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            model_locked
        FROM predictions
        WHERE id = ?
          AND match_id = ?
        LIMIT 1
        """,
        (
            INVALID_PREDICTION_ID,
            match_id,
        ),
    )

    verified_prediction = cursor.fetchone()

    if verified_prediction is None:

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Prediction silinmiş."
        )

    if int(
        verified_prediction["model_locked"]
    ) != 1:

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Prediction model lock değişmiş."
        )

    # -----------------------------------------------------
    # 12. VERIFY MATCH
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            status,
            final_home_score,
            final_away_score
        FROM matches
        WHERE id = ?
          AND statshub_fixture_id = ?
        LIMIT 1
        """,
        (
            match_id,
            FIXTURE_ID,
        ),
    )

    verified_match = cursor.fetchone()

    if verified_match is None:

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Match kaydı bulunamadı."
        )

    if verified_match["status"] != "notstarted":

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Match status notstarted değil."
        )

    if (
        verified_match["final_home_score"]
        is not None
        or
        verified_match["final_away_score"]
        is not None
    ):

        conn.close()

        raise SystemExit(
            "CLEANUP VALIDATION ERROR: "
            "Final skor temizlenmemiş."
        )

    # -----------------------------------------------------
    # 13. TOTAL COUNTS
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

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM settlements
        WHERE prediction_id = ?
        """,
        (INVALID_PREDICTION_ID,),
    )

    settlement_count = cursor.fetchone()[0]

    conn.close()

    # -----------------------------------------------------
    # 14. FINAL
    # -----------------------------------------------------

    print("")
    print("==========================================")
    print("CLEANUP VALIDATION: PASS")
    print("==========================================")
    print("")

    print(
        "Deleted settlement:",
        deleted_count
    )

    print(
        "Remaining settlement for Prediction 1:",
        settlement_count
    )

    print(
        "Prediction preserved:",
        prediction_count
    )

    print(
        "Model lock: PRESERVED"
    )

    print(
        "Match status: notstarted"
    )

    print(
        "Final score: NULL - NULL"
    )

    print("")
    print(
        "SAFE CLEANUP COMPLETE"
    )
    print("")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
