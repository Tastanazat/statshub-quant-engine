import json
import os
import statistics
from datetime import datetime, timezone

# ============================================================
# STATSHUB QUANT ANALYSIS ENGINE
# ============================================================

INPUT_FILE = "data/statshub_team_stats.json"

OUTPUT_FILE = "data/statshub_team_analysis.json"

TEAMS = {
    "PSV": 2952,
    "Shakhtar": 3313
}

# ============================================================
# DOSYAYI OKU
# ============================================================

if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"Dosya bulunamadı: {INPUT_FILE}"
    )

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    source = json.load(f)


# ============================================================
# SAYIYA ÇEVİR
# ============================================================

def to_number(value):

    try:

        if value is None:
            return None

        return float(value)

    except Exception:

        return None


# ============================================================
# TAKIMIN MAÇLARINI ÇIKAR
# ============================================================

def extract_team_matches(
    team_name,
    team_id,
    stat_data
):

    if not isinstance(stat_data, dict):

        return []

    raw = stat_data.get("data")

    if not isinstance(raw, dict):

        return []

    matches = raw.get("data")

    if not isinstance(matches, list):

        return []

    result = []

    for match in matches:

        if not isinstance(match, dict):
            continue

        home_id = match.get(
            "home_team_id"
        )

        away_id = match.get(
            "away_team_id"
        )

        # ----------------------------------------------------
        # Takımın hangi tarafta olduğunu belirle
        # ----------------------------------------------------

        if home_id == team_id:

            location = "home"

            value = match.get(
                "home_value"
            )

            opponent = match.get(
                "away_team_name"
            )

            opponent_id = away_id

            team_score = match.get(
                "home_score"
            )

            opponent_score = match.get(
                "away_score"
            )

        elif away_id == team_id:

            location = "away"

            value = match.get(
                "away_value"
            )

            opponent = match.get(
                "home_team_name"
            )

            opponent_id = home_id

            team_score = match.get(
                "away_score"
            )

            opponent_score = match.get(
                "home_score"
            )

        else:

            continue

        numeric_value = to_number(
            value
        )

        # ----------------------------------------------------
        # Sonucu belirle
        # ----------------------------------------------------

        result_status = "N/A"

        if (
            isinstance(team_score, int)
            and isinstance(opponent_score, int)
        ):

            if team_score > opponent_score:
                result_status = "W"

            elif team_score < opponent_score:
                result_status = "L"

            else:
                result_status = "D"

        # ----------------------------------------------------
        # Tarih
        # ----------------------------------------------------

        timestamp = match.get(
            "time_start_timestamp"
        )

        date_text = None

        try:

            if timestamp:

                date_text = datetime.fromtimestamp(
                    int(timestamp),
                    tz=timezone.utc
                ).strftime(
                    "%Y-%m-%d"
                )

        except Exception:

            pass

        result.append({

            "event_id": match.get(
                "event_id"
            ),

            "date": date_text,

            "team": team_name,

            "team_id": team_id,

            "location": location,

            "opponent": opponent,

            "opponent_id": opponent_id,

            "team_score": team_score,

            "opponent_score": opponent_score,

            "result": result_status,

            "value": numeric_value,

            "league": match.get(
                "league_name"
            ),

            "league_id": match.get(
                "league_id"
            )

        })

    return result


# ============================================================
# İSTATİSTİK ANALİZİ
# ============================================================

def calculate_statistics(matches):

    values = []

    for match in matches:

        value = match.get(
            "value"
        )

        if value is not None:

            values.append(
                value
            )

    if not values:

        return {

            "available": False,

            "count": 0,

            "average": None,

            "median": None,

            "minimum": None,

            "maximum": None

        }

    return {

        "available": True,

        "count": len(values),

        "average": round(
            statistics.mean(values),
            4
        ),

        "median": round(
            statistics.median(values),
            4
        ),

        "minimum": round(
            min(values),
            4
        ),

        "maximum": round(
            max(values),
            4
        )

    }


# ============================================================
# ANALİZ NESNESİ
# ============================================================

analysis = {

    "source": "StatsHub",

    "fixture_id": source.get(
        "fixture_id"
    ),

    "teams": TEAMS,

    "statistics": {},

    "team_analysis": {}

}


# ============================================================
# TAKIMLAR
# ============================================================

for team_name, team_id in TEAMS.items():

    print("")
    print(
        "================================"
    )
    print(team_name)
    print(
        "================================"
    )

    analysis[
        "team_analysis"
    ][team_name] = {

        "team_id": team_id,

        "statistics": {}

    }

    for stat_name, stat_info in source[
        "data"
    ][team_name].items():

        print(
            f"{stat_name} ...",
            end=" "
        )

        matches = extract_team_matches(
            team_name,
            team_id,
            stat_info
        )

        stats = calculate_statistics(
            matches
        )

        analysis[
            "team_analysis"
        ][team_name][
            "statistics"
        ][stat_name] = {

            "statistic_key":
                stat_info.get(
                    "statistic_key"
                ),

            "status_code":
                stat_info.get(
                    "status_code"
                ),

            "available":
                stats[
                    "available"
                ],

            "count":
                stats[
                    "count"
                ],

            "average":
                stats[
                    "average"
                ],

            "median":
                stats[
                    "median"
                ],

            "minimum":
                stats[
                    "minimum"
                ],

            "maximum":
                stats[
                    "maximum"
                ],

            "matches":
                matches

        }

        if stats["available"]:

            print(
                "OK",
                stats["count"],
                "maç"
            )

        else:

            print(
                "N/A"
            )


# ============================================================
# EV / DEPLASMAN AYRIMI
# ============================================================

for team_name in analysis[
    "team_analysis"
]:

    stats_dict = analysis[
        "team_analysis"
    ][team_name][
        "statistics"
    ]

    for stat_name, stat_info in stats_dict.items():

        matches = stat_info[
            "matches"
        ]

        home_matches = [
            m for m in matches
            if m["location"] == "home"
        ]

        away_matches = [
            m for m in matches
            if m["location"] == "away"
        ]

        stat_info[
            "home_average"
        ] = calculate_statistics(
            home_matches
        )["average"]

        stat_info[
            "away_average"
        ] = calculate_statistics(
            away_matches
        )["average"]

        stat_info[
            "home_count"
        ] = len([
            m for m in home_matches
            if m["value"] is not None
        ])

        stat_info[
            "away_count"
        ] = len([
            m for m in away_matches
            if m["value"] is not None
        ])


# ============================================================
# KAYDET
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        analysis,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# ÖZET
# ============================================================

print("")
print("")
print("==========================================")
print("STATSHUB ANALİZ TAMAMLANDI")
print("==========================================")
print("")

for team_name in TEAMS:

    print(
        team_name
    )

    stats_dict = analysis[
        "team_analysis"
    ][team_name][
        "statistics"
    ]

    available_count = 0

    for stat_name, stat_info in stats_dict.items():

        if stat_info[
            "available"
        ]:

            available_count += 1

    print(
        "Kullanılabilir istatistik:",
        available_count,
        "/",
        len(stats_dict)
    )

    print("")

print(
    "Çıktı:"
)

print(
    OUTPUT_FILE
)

print("")
