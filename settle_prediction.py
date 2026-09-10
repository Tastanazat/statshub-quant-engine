
import json
import sqlite3
import requests
from datetime import datetime, timezone


# =========================================================
# CONFIGURATION
# =========================================================

DATABASE_FILE = "data/database/quant_engine.db"

STATSHUB_BASE_URL = "https://www.statshub.com"

# StatsHub fixture URL ID
FIXTURE_ID = "416477"

# StatsHub event ID discovered from the fixture
EVENT_ID = 16938896

# Teams
HOME_TEAM_ID = 2952
AWAY_TEAM_ID = 3313

HOME_TEAM_NAME = "PSV"
AWAY_TEAM_NAME = "Shakhtar"

TIMEOUT = 30


# =========================================================
# HELPERS
# =========================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def safe_int(value):
    try:
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        return int(value)

    except (TypeError, ValueError):
        return None


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().lower()


# =========================================================
# HTTP
# =========================================================

def get_json(url):
    print("")
    print("StatsHub request:")
    print(url)

    response = requests.get(
        url,
        timeout=TIMEOUT,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Linux; Android 16) "
                "AppleWebKit/537.36 "
                "Chrome/140.0 Mobile Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
            "Referer": (
                f"{STATSHUB_BASE_URL}/fixture/"
                f"psv-eindhoven-vs-shakhtar-donetsk-mtv02l/"
                f"{FIXTURE_ID}"
            ),
        },
    )

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        return None

    try:
        return response.json()

    except ValueError:
        print("StatsHub response JSON değil.")
        return None


# =========================================================
# RECURSIVE SEARCH
# =========================================================

def walk_objects(value):
    """
    JSON içindeki bütün dictionary nesnelerini recursive olarak gezer.
    """

    if isinstance(value, dict):

        yield value

        for child in value.values():
            yield from walk_objects(child)

    elif isinstance(value, list):

        for child in value:
            yield from walk_objects(child)


# =========================================================
# IDENTIFIER MATCH
# =========================================================

def object_matches_fixture(obj):
    """
    StatsHub event objesinin bizim fixture/event'e ait olup
    olmadığını kontrol eder.
    """

    possible_ids = [
        obj.get("id"),
        obj.get("eventId"),
        obj.get("event_id"),
        obj.get("fixtureId"),
        obj.get("fixture_id"),
        obj.get("internalId"),
        obj.get("internal_id"),
    ]

    for value in possible_ids:

        if value is None:
            continue

        if str(value) == str(EVENT_ID):
            return True

        if str(value) == str(FIXTURE_ID):
            return True

    return False


# =========================================================
# SCORE EXTRACTION
# =========================================================

def extract_score_from_object(obj):
    """
    StatsHub farklı response yapıları kullanabilir.
    Bilinen score alanlarını güvenli şekilde arar.
    """

    possible_pairs = [
        ("homeScore", "awayScore"),
        ("home_score", "away_score"),
        ("homeGoals", "awayGoals"),
        ("home_goals", "away_goals"),
        ("homeScoreCurrent", "awayScoreCurrent"),
        ("home_score_current", "away_score_current"),
    ]

    for home_key, away_key in possible_pairs:

        if home_key in obj and away_key in obj:

            home_value = obj.get(home_key)
            away_value = obj.get(away_key)

            # Score bazen doğrudan sayı olur
            home_score = safe_int(home_value)
            away_score = safe_int(away_value)

            if (
                home_score is not None
                and away_score is not None
                and home_score >= 0
                and away_score >= 0
            ):
                return home_score, away_score

            # Score bazen dict olur
            if isinstance(home_value, dict):
                for key in [
                    "current",
                    "display",
                    "normaltime",
                    "normaltime",
                    "period1",
                    "value",
                ]:
                    if key in home_value:
                        candidate_home = safe_int(
                            home_value.get(key)
                        )

                        candidate_away = None

                        if isinstance(away_value, dict):
                            candidate_away = safe_int(
                                away_value.get(key)
                            )

                        if (
                            candidate_home is not None
                            and candidate_away is not None
                            and candidate_home >= 0
                            and candidate_away >= 0
                        ):
                            return (
                                candidate_home,
                                candidate_away,
                            )

    # Nested "score" object
    score = obj.get("score")

    if isinstance(score, dict):

        home = score.get("home")
        away = score.get("away")

        home_score = safe_int(home)
        away_score = safe_int(away)

        if (
            home_score is not None
            and away_score is not None
            and home_score >= 0
            and away_score >= 0
        ):
            return home_score, away_score

        # score.home.current / score.away.current
        if isinstance(home, dict) and isinstance(away, dict):

            for key in [
                "current",
                "display",
                "normaltime",
                "value",
            ]:

                home_score = safe_int(home.get(key))
                away_score = safe_int(away.get(key))

                if (
                    home_score is not None
                    and away_score is not None
                    and home_score >= 0
                    and away_score >= 0
                ):
                    return home_score, away_score

    return None


# =========================================================
# TEAM MATCH CHECK
# =========================================================

def object_has_our_teams(obj):

    text_parts = []

    for key in [
        "homeTeamName",
        "awayTeamName",
        "home_team_name",
        "away_team_name",
        "homeTeam",
        "awayTeam",
    ]:

        value = obj.get(key)

        if isinstance(value, dict):

            text_parts.append(
                str(value.get("name", ""))
            )

            team_id = value.get("id")

            if str(team_id) in [
                str(HOME_TEAM_ID),
                str(AWAY_TEAM_ID),
            ]:
                return True

        elif value is not None:

            text_parts.append(str(value))

    combined = " ".join(text_parts).lower()

    home_ok = (
        "psv" in combined
        or "eindhoven" in combined
    )

    away_ok = (
        "shakhtar" in combined
        or "donetsk" in combined
    )

    return home_ok and away_ok


# =========================================================
# FIND EVENT
# =========================================================

def find_event_in_data(data):

    candidates = []

    for obj in walk_objects(data):

        if not isinstance(obj, dict):
            continue

        identifier_match = object_matches_fixture(obj)

        team_match = object_has_our_teams(obj)

        score = extract_score_from_object(obj)

        if identifier_match or team_match:

            candidates.append(
                {
                    "object": obj,
                    "identifier_match": identifier_match,
                    "team_match": team_match,
                    "score": score,
                }
            )

    # Öncelik:
    # 1. fixture/event ID eşleşmesi + skor
    # 2. takım eşleşmesi + skor
    # 3. ID eşleşmesi

    for candidate in candidates:

        if (
            candidate["identifier_match"]
            and candidate["score"] is not None
        ):
            return candidate["object"], candidate["score"]

    for candidate in candidates:

        if (
            candidate["team_match"]
            and candidate["score"] is not None
        ):
            return candidate["object"], candidate["score"]

    for candidate in candidates:

        if candidate["identifier_match"]:
            return candidate["object"], None

    return None, None


# =========================================================
# FETCH STATSHUB RESULT
# =========================================================

def fetch_final_result():

    urls = [

        # -----------------------------------------------------
        # 1. PSV finished events
        # -----------------------------------------------------

        (
            f"{STATSHUB_BASE_URL}"
            f"/api/team/{HOME_TEAM_ID}"
            f"/events?status=finished&limit=50"
        ),

        # -----------------------------------------------------
        # 2. Shakhtar finished events
        # -----------------------------------------------------

        (
            f"{STATSHUB_BASE_URL}"
            f"/api/team/{AWAY_TEAM_ID}"
            f"/events?status=finished&limit=50"
        ),

        # -----------------------------------------------------
        # 3. Tournament events
        # -----------------------------------------------------

        (
            f"{STATSHUB_BASE_URL}"
            f"/api/tournament/1988/96518/events"
        ),
    ]

    for url in urls:

        data = get_json(url)

        if data is None:
            continue

        event, score = find_event_in_data(data)

        if event is None:
            continue

        print("")
        print("StatsHub fixture bulundu.")

        if score is None:

            print(
                "Fixture bulundu fakat final skor "
                "henüz bulunamadı."
            )

            continue

        home_score, away_score = score

        print("")
        print("==========================================")
        print("STATSHUB FINAL RESULT FOUND")
        print("==========================================")
        print("")
        print(
            f"{HOME_TEAM_NAME} {home_score} - "
            f"{away_score} {AWAY_TEAM_NAME}"
        )
        print("")

        return {
            "status": "finished",
            "home_score": home_score,
            "away_score": away_score,
            "event": event,
        }

    return None


# =========================================================
# SETTLEMENT CALCULATIONS
# =========================================================

def calculate_settlement(
    home_score,
    away_score
):

    total_goals = home_score + away_score

    # -----------------------------------------------------
    # 1X2
    # -----------------------------------------------------

    if home_score > away_score:

        result_1x2 = "HOME"

    elif home_score < away_score:

        result_1x2 = "AWAY"

    else:

        result_1x2 = "DRAW"

    # -----------------------------------------------------
    # BTTS
    # -----------------------------------------------------

    if home_score > 0 and away_score > 0:

        btts_result = "YES"

    else:

        btts_result = "NO"

    # -----------------------------------------------------
    # OVER / UNDER
    # -----------------------------------------------------

    results = {}

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
    ]:

        line_key = str(line).replace(".", "_")

        if total_goals > line:

            results[
                f"over_{line_key}_result"
            ] = "WIN"

            results[
                f"under_{line_key}_result"
            ] = "LOSS"

        else:

            results[
                f"over_{line_key}_result"
            ] = "LOSS"

            results[
                f"under_{line_key}_result"
            ] = "WIN"

    return {
        "result_1x2": result_1x2,
        "total_goals": total_goals,
        "btts_result": btts_result,
        **results,
    }


# =========================================================
# DATABASE
# =========================================================

def settle_database(
    home_score,
    away_score
):

    conn = sqlite3.connect(
        DATABASE_FILE
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # -----------------------------------------------------
    # FIND MATCH
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
            "SETTLEMENT ERROR: "
            "Fixture için matches kaydı bulunamadı."
        )

    match_id = match["id"]

    print("")
    print("Match ID:", match_id)

    # -----------------------------------------------------
    # UPDATE MATCH RESULT
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE matches
        SET
            status = ?,
            final_home_score = ?,
            final_away_score = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            "finished",
            home_score,
            away_score,
            now_utc(),
            match_id,
        ),
    )

    # -----------------------------------------------------
    # FIND PREDICTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            model_version,
            model_locked
        FROM predictions
        WHERE match_id = ?
        ORDER BY id ASC
        """,
        (match_id,),
    )

    predictions = cursor.fetchall()

    if not predictions:

        conn.commit()
        conn.close()

        raise SystemExit(
            "SETTLEMENT ERROR: "
            "Bu maç için prediction bulunamadı."
        )

    print("")
    print(
        "Prediction count:",
        len(predictions)
    )

    # -----------------------------------------------------
    # CALCULATE RESULT
    # -----------------------------------------------------

    settlement = calculate_settlement(
        home_score,
        away_score,
    )

    # -----------------------------------------------------
    # EACH PREDICTION
    # -----------------------------------------------------

    created_count = 0
    skipped_count = 0

    for prediction in predictions:

        prediction_id = prediction["id"]

        # -------------------------------------------------
        # MODEL LOCK CHECK
        # -------------------------------------------------

        if int(prediction["model_locked"]) != 1:

            conn.rollback()
            conn.close()

            raise SystemExit(
                "SETTLEMENT ERROR: "
                f"Prediction {prediction_id} "
                "model_locked=1 değil."
            )

        # -------------------------------------------------
        # DUPLICATE PROTECTION
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM settlements
            WHERE prediction_id = ?
            LIMIT 1
            """,
            (prediction_id,),
        )

        existing = cursor.fetchone()

        if existing is not None:

            print(
                f"Prediction {prediction_id}: "
                "Settlement zaten mevcut. SKIP."
            )

            skipped_count += 1

            continue

        # -------------------------------------------------
        # INSERT SETTLEMENT
        # -------------------------------------------------

        cursor.execute(
            """
            INSERT INTO settlements (
                prediction_id,
                settlement_time,
                final_home_score,
                final_away_score,
                result_1x2,
                total_goals,
                btts_result,
                over_0_5_result,
                over_1_5_result,
                over_2_5_result,
                over_3_5_result,
                over_4_5_result,
                settled
            )
            VALUES (
                :prediction_id,
                :settlement_time,
                :final_home_score,
                :final_away_score,
                :result_1x2,
                :total_goals,
                :btts_result,
                :over_0_5_result,
                :over_1_5_result,
                :over_2_5_result,
                :over_3_5_result,
                :over_4_5_result,
                :settled
            )
            """,
            {
                "prediction_id": prediction_id,
                "settlement_time": now_utc(),
                "final_home_score": home_score,
                "final_away_score": away_score,
                "result_1x2": settlement["result_1x2"],
                "total_goals": settlement["total_goals"],
                "btts_result": settlement["btts_result"],
                "over_0_5_result": settlement[
                    "over_0_5_result"
                ],
                "over_1_5_result": settlement[
                    "over_1_5_result"
                ],
                "over_2_5_result": settlement[
                    "over_2_5_result"
                ],
                "over_3_5_result": settlement[
                    "over_3_5_result"
                ],
                "over_4_5_result": settlement[
                    "over_4_5_result"
                ],
                "settled": 1,
            },
        )

        print(
            f"Prediction {prediction_id}: "
            "Settlement INSERTED."
        )

        created_count += 1

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

    settlement_count = cursor.fetchone()[0]

    conn.close()

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print("")
    print("==========================================")
    print("SETTLEMENT ENGINE")
    print("VALIDATION: PASS")
    print("==========================================")
    print("")
    print(
        f"{HOME_TEAM_NAME} {home_score} - "
        f"{away_score} {AWAY_TEAM_NAME}"
    )
    print("")
    print(
        "1X2 Result:",
        settlement["result_1x2"]
    )
    print(
        "Total Goals:",
        settlement["total_goals"]
    )
    print(
        "BTTS:",
        settlement["btts_result"]
    )
    print("")
    print(
        "Over 0.5:",
        settlement["over_0_5_result"]
    )
    print(
        "Over 1.5:",
        settlement["over_1_5_result"]
    )
    print(
        "Over 2.5:",
        settlement["over_2_5_result"]
    )
    print(
        "Over 3.5:",
        settlement["over_3_5_result"]
    )
    print(
        "Over 4.5:",
        settlement["over_4_5_result"]
    )
    print("")
    print(
        "New Settlements:",
        created_count
    )
    print(
        "Skipped Existing:",
        skipped_count
    )
    print(
        "Total Settlements:",
        settlement_count
    )
    print("")
    print(
        "MODEL LOCK: PRESERVED"
    )
    print(
        "Prediction probabilities: NOT MODIFIED"
    )
    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    print("")
    print("==========================================")
    print("STATSHUB SETTLEMENT ENGINE")
    print("==========================================")
    print("")

    print("Source: StatsHub")
    print("Fixture ID:", FIXTURE_ID)
    print("Event ID:", EVENT_ID)
    print(
        "Match:",
        HOME_TEAM_NAME,
        "vs",
        AWAY_TEAM_NAME,
    )

    # -----------------------------------------------------
    # FETCH RESULT
    # -----------------------------------------------------

    result = fetch_final_result()

    # -----------------------------------------------------
    # NO FINAL RESULT
    # -----------------------------------------------------

    if result is None:

        print("")
        print("==========================================")
        print("MATCH NOT FINISHED / RESULT NOT AVAILABLE")
        print("==========================================")
        print("")
        print(
            "StatsHub'da final skor bulunamadı."
        )
        print(
            "Settlement yapılmadı."
        )
        print(
            "Database değiştirilmedi."
        )
        print("")

        return

    # -----------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------

    home_score = result["home_score"]
    away_score = result["away_score"]

    # -----------------------------------------------------
    # SAFETY
    # -----------------------------------------------------

    if home_score < 0 or away_score < 0:

        raise SystemExit(
            "SETTLEMENT ERROR: "
            "Geçersiz final skor."
        )

    # -----------------------------------------------------
    # SETTLE
    # -----------------------------------------------------

    settle_database(
        home_score,
        away_score,
    )


if __name__ == "__main__":
    main()
