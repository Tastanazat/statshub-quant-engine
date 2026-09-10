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

# EXACT StatsHub event ID
EVENT_ID = 16938896

# Teams
HOME_TEAM_ID = 2952
AWAY_TEAM_ID = 3313

HOME_TEAM_NAME = "PSV"
AWAY_TEAM_NAME = "Shakhtar"

TIMEOUT = 30


# =========================================================
# TIME
# =========================================================

def now_utc():
    return datetime.now(timezone.utc).isoformat()


# =========================================================
# SAFE INTEGER
# =========================================================

def safe_int(value):

    try:

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        return int(value)

    except (TypeError, ValueError):

        return None


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

        print(
            "StatsHub HTTP ERROR:",
            response.status_code
        )

        return None

    try:

        return response.json()

    except ValueError:

        print(
            "StatsHub response JSON değil."
        )

        return None


# =========================================================
# RECURSIVE JSON WALKER
# =========================================================

def walk_objects(value):

    if isinstance(value, dict):

        yield value

        for child in value.values():

            yield from walk_objects(child)

    elif isinstance(value, list):

        for child in value:

            yield from walk_objects(child)


# =========================================================
# EXACT EVENT ID CHECK
# =========================================================

def has_exact_event_id(obj):

    possible_id_fields = [
        "id",
        "eventId",
        "event_id",
        "fixtureId",
        "fixture_id",
        "internalId",
        "internal_id",
    ]

    for field in possible_id_fields:

        value = obj.get(field)

        if value is None:
            continue

        if str(value) == str(EVENT_ID):

            return True

    return False


# =========================================================
# STATUS EXTRACTION
# =========================================================

def extract_status(obj):

    possible_fields = [
        "status",
        "eventStatus",
        "event_status",
        "matchStatus",
        "match_status",
    ]

    for field in possible_fields:

        value = obj.get(field)

        if value is None:
            continue

        if isinstance(value, str):

            return value.strip().lower()

        if isinstance(value, dict):

            for key in [
                "type",
                "name",
                "description",
                "code",
                "status",
            ]:

                nested = value.get(key)

                if nested is not None:

                    return str(
                        nested
                    ).strip().lower()

    return None


# =========================================================
# SCORE EXTRACTION
# =========================================================

def extract_score(obj):

    # -----------------------------------------------------
    # DIRECT SCORE FIELDS
    # -----------------------------------------------------

    possible_pairs = [

        (
            "homeScore",
            "awayScore"
        ),

        (
            "home_score",
            "away_score"
        ),

        (
            "homeGoals",
            "awayGoals"
        ),

        (
            "home_goals",
            "away_goals"
        ),

        (
            "homeScoreCurrent",
            "awayScoreCurrent"
        ),

        (
            "home_score_current",
            "away_score_current"
        ),
    ]

    for home_key, away_key in possible_pairs:

        if (
            home_key in obj
            and away_key in obj
        ):

            home_score = safe_int(
                obj.get(home_key)
            )

            away_score = safe_int(
                obj.get(away_key)
            )

            if (
                home_score is not None
                and away_score is not None
                and home_score >= 0
                and away_score >= 0
            ):

                return (
                    home_score,
                    away_score
                )

    # -----------------------------------------------------
    # SCORE OBJECT
    # -----------------------------------------------------

    score = obj.get("score")

    if isinstance(score, dict):

        # score.home / score.away
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

            return (
                home_score,
                away_score
            )

        # Nested score objects
        if (
            isinstance(home, dict)
            and isinstance(away, dict)
        ):

            for key in [
                "current",
                "display",
                "normaltime",
                "value",
                "period1",
            ]:

                home_score = safe_int(
                    home.get(key)
                )

                away_score = safe_int(
                    away.get(key)
                )

                if (
                    home_score is not None
                    and away_score is not None
                    and home_score >= 0
                    and away_score >= 0
                ):

                    return (
                        home_score,
                        away_score
                    )

    return None


# =========================================================
# TEAM VALIDATION
# =========================================================

def validate_teams(obj):

    home_id = None
    away_id = None

    # -----------------------------------------------------
    # DIRECT TEAM IDs
    # -----------------------------------------------------

    possible_home_id_fields = [
        "homeTeamId",
        "home_team_id",
    ]

    possible_away_id_fields = [
        "awayTeamId",
        "away_team_id",
    ]

    for field in possible_home_id_fields:

        if obj.get(field) is not None:

            home_id = safe_int(
                obj.get(field)
            )

            break

    for field in possible_away_id_fields:

        if obj.get(field) is not None:

            away_id = safe_int(
                obj.get(field)
            )

            break

    # -----------------------------------------------------
    # NESTED TEAM OBJECTS
    # -----------------------------------------------------

    home_team = obj.get("homeTeam")

    away_team = obj.get("awayTeam")

    if isinstance(home_team, dict):

        if home_id is None:

            home_id = safe_int(
                home_team.get("id")
            )

    if isinstance(away_team, dict):

        if away_id is None:

            away_id = safe_int(
                away_team.get("id")
            )

    # -----------------------------------------------------
    # EXACT TEAM ID VALIDATION
    # -----------------------------------------------------

    if (
        home_id == HOME_TEAM_ID
        and away_id == AWAY_TEAM_ID
    ):

        return True

    return False


# =========================================================
# FIND EXACT EVENT
# =========================================================

def find_exact_event(data):

    candidates = []

    for obj in walk_objects(data):

        if not isinstance(obj, dict):

            continue

        # -------------------------------------------------
        # ABSOLUTE REQUIREMENT #1
        # -------------------------------------------------

        if not has_exact_event_id(obj):

            continue

        # -------------------------------------------------
        # ABSOLUTE REQUIREMENT #2
        # -------------------------------------------------

        team_match = validate_teams(obj)

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score = extract_score(obj)

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        status = extract_status(obj)

        candidates.append(
            {
                "object": obj,
                "team_match": team_match,
                "score": score,
                "status": status,
            }
        )

    print("")
    print(
        "Exact EVENT_ID candidates:",
        len(candidates)
    )

    # -----------------------------------------------------
    # REQUIRE EXACT EVENT + EXACT TEAMS
    # -----------------------------------------------------

    for candidate in candidates:

        if candidate["team_match"]:

            return candidate

    # -----------------------------------------------------
    # EVENT FOUND BUT TEAM STRUCTURE DIFFERENT
    # -----------------------------------------------------

    if candidates:

        print(
            "EVENT_ID bulundu fakat "
            "home/away team ID doğrulanamadı."
        )

        return candidates[0]

    return None


# =========================================================
# FETCH EXACT STATSHUB EVENT
# =========================================================

def fetch_final_result():

    # -----------------------------------------------------
    # PRIMARY SOURCE
    #
    # Exact tournament event list.
    # We DO NOT accept a random team event.
    # -----------------------------------------------------

    url = (
        f"{STATSHUB_BASE_URL}"
        f"/api/tournament/1988/96518/events"
    )

    data = get_json(url)

    if data is None:

        return None

    candidate = find_exact_event(data)

    if candidate is None:

        print("")
        print(
            "EXACT EVENT NOT FOUND."
        )

        return None

    event = candidate["object"]

    score = candidate["score"]

    status = candidate["status"]

    print("")
    print("==========================================")
    print("EXACT STATSHUB EVENT FOUND")
    print("==========================================")
    print("")
    print(
        "Required Event ID:",
        EVENT_ID
    )
    print(
        "Required Fixture ID:",
        FIXTURE_ID
    )
    print(
        "Status:",
        status
    )
    print(
        "Team IDs validated:",
        candidate["team_match"]
    )

    # -----------------------------------------------------
    # EVENT ID SAFETY
    # -----------------------------------------------------

    if not has_exact_event_id(event):

        print(
            "SECURITY ERROR: Exact Event ID "
            "verification failed."
        )

        return None

    # -----------------------------------------------------
    # TEAM SAFETY
    # -----------------------------------------------------

    if not candidate["team_match"]:

        print(
            "SECURITY ERROR: Home/Away team IDs "
            "do not match target fixture."
        )

        return None

    # -----------------------------------------------------
    # STATUS SAFETY
    # -----------------------------------------------------

    if status is None:

        print(
            "StatsHub event status bulunamadı."
        )

        print(
            "Settlement yapılmayacak."
        )

        return None

    finished_statuses = {
        "finished",
        "ended",
        "ft",
        "afterpenalties",
        "aet",
        "fulltime",
        "full time",
    }

    if status not in finished_statuses:

        print("")
        print(
            "MATCH NOT FINISHED."
        )
        print(
            "StatsHub status:",
            status
        )
        print(
            "Settlement yapılmayacak."
        )

        return None

    # -----------------------------------------------------
    # SCORE SAFETY
    # -----------------------------------------------------

    if score is None:

        print(
            "StatsHub final score bulunamadı."
        )

        print(
            "Settlement yapılmayacak."
        )

        return None

    home_score, away_score = score

    if (
        home_score < 0
        or away_score < 0
    ):

        print(
            "Geçersiz skor."
        )

        return None

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    print("")
    print(
        "STATSHUB FINAL RESULT CONFIRMED"
    )
    print("")
    print(
        f"{HOME_TEAM_NAME} "
        f"{home_score} - "
        f"{away_score} "
        f"{AWAY_TEAM_NAME}"
    )
    print("")

    return {
        "status": "finished",
        "home_score": home_score,
        "away_score": away_score,
        "event": event,
    }


# =========================================================
# SETTLEMENT CALCULATION
# =========================================================

def calculate_settlement(
    home_score,
    away_score
):

    total_goals = (
        home_score
        + away_score
    )

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

    if (
        home_score > 0
        and away_score > 0
    ):

        btts_result = "YES"

    else:

        btts_result = "NO"

    # -----------------------------------------------------
    # O/U
    # -----------------------------------------------------

    results = {}

    for line in [
        0.5,
        1.5,
        2.5,
        3.5,
        4.5,
    ]:

        key = str(line).replace(
            ".",
            "_"
        )

        if total_goals > line:

            results[
                f"over_{key}_result"
            ] = "WIN"

            results[
                f"under_{key}_result"
            ] = "LOSS"

        else:

            results[
                f"over_{key}_result"
            ] = "LOSS"

            results[
                f"under_{key}_result"
            ] = "WIN"

    return {
        "result_1x2": result_1x2,
        "total_goals": total_goals,
        "btts_result": btts_result,
        **results,
    }


# =========================================================
# DATABASE SETTLEMENT
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
            "SETTLEMENT ERROR: "
            "Fixture matches tablosunda bulunamadı."
        )

    match_id = match["id"]

    print("")
    print(
        "Database Match ID:",
        match_id
    )

    # -----------------------------------------------------
    # DATABASE TEAM SAFETY
    # -----------------------------------------------------

    if (
        str(match["home_team"]).lower()
        != HOME_TEAM_NAME.lower()
        or
        str(match["away_team"]).lower()
        != AWAY_TEAM_NAME.lower()
    ):

        conn.close()

        raise SystemExit(
            "SETTLEMENT SECURITY ERROR: "
            "Database home/away takımları hedef "
            "fixture ile eşleşmiyor."
        )

    # -----------------------------------------------------
    # UPDATE MATCH
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

        conn.rollback()
        conn.close()

        raise SystemExit(
            "SETTLEMENT ERROR: "
            "Bu maç için prediction bulunamadı."
        )

    print(
        "Prediction count:",
        len(predictions)
    )

    # -----------------------------------------------------
    # CALCULATE
    # -----------------------------------------------------

    settlement = calculate_settlement(
        home_score,
        away_score,
    )

    created_count = 0
    skipped_count = 0

    # -----------------------------------------------------
    # SETTLE EACH PREDICTION
    # -----------------------------------------------------

    for prediction in predictions:

        prediction_id = prediction["id"]

        # -------------------------------------------------
        # MODEL LOCK MUST REMAIN
        # -------------------------------------------------

        if int(
            prediction["model_locked"]
        ) != 1:

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
        # INSERT
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
                "result_1x2": settlement[
                    "result_1x2"
                ],
                "total_goals": settlement[
                    "total_goals"
                ],
                "btts_result": settlement[
                    "btts_result"
                ],
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
    # VERIFY SETTLEMENT
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

    # -----------------------------------------------------
    # VERIFY MATCH
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT
            status,
            final_home_score,
            final_away_score
        FROM matches
        WHERE id = ?
        LIMIT 1
        """,
        (match_id,),
    )

    verified_match = cursor.fetchone()

    conn.close()

    # -----------------------------------------------------
    # FINAL VALIDATION
    # -----------------------------------------------------

    if verified_match is None:

        raise SystemExit(
            "SETTLEMENT VALIDATION ERROR: "
            "Match verification başarısız."
        )

    if verified_match["status"] != "finished":

        raise SystemExit(
            "SETTLEMENT VALIDATION ERROR: "
            "Match status finished değil."
        )

    if (
        int(
            verified_match["final_home_score"]
        )
        != home_score
        or
        int(
            verified_match["final_away_score"]
        )
        != away_score
    ):

        raise SystemExit(
            "SETTLEMENT VALIDATION ERROR: "
            "Database final skor doğrulaması başarısız."
        )

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
        f"{HOME_TEAM_NAME} "
        f"{home_score} - "
        f"{away_score} "
        f"{AWAY_TEAM_NAME}"
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

    print(
        "Source: StatsHub"
    )

    print(
        "Fixture ID:",
        FIXTURE_ID
    )

    print(
        "Event ID:",
        EVENT_ID
    )

    print(
        "Match:",
        HOME_TEAM_NAME,
        "vs",
        AWAY_TEAM_NAME
    )

    # -----------------------------------------------------
    # FETCH EXACT RESULT
    # -----------------------------------------------------

    result = fetch_final_result()

    # -----------------------------------------------------
    # NO VALID FINAL RESULT
    # -----------------------------------------------------

    if result is None:

        print("")
        print("==========================================")
        print("NO VALID FINAL RESULT")
        print("==========================================")
        print("")
        print(
            "Settlement yapılmadı."
        )
        print(
            "Prediction değiştirilmedi."
        )
        print("")

        return

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    home_score = result[
        "home_score"
    ]

    away_score = result[
        "away_score"
    ]

    # -----------------------------------------------------
    # SETTLE
    # -----------------------------------------------------

    settle_database(
        home_score,
        away_score,
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()
