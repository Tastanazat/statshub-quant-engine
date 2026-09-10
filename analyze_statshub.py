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
# SKORU INTEGER'A ÇEVİR
# ============================================================

def to_score(value):

    try:
        if value is None:
            return None

        return int(value)

    except Exception:
        return None


# ============================================================
# TAKIM MAÇLARINI ÇIKAR
# ============================================================

def extract_team_matches(
    team_name,
    team_id,
    stat_info
):

    if not isinstance(stat_info, dict):
        return []

    raw = stat_info.get("data")

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

        # ====================================================
        # EV SAHİBİ
        # ====================================================

        if home_id == team_id:

            location = "home"

            value = match.get(
                "home_value"
            )

            opponent = match.get(
                "away_team_name"
            )

            opponent_id = away_id

            team_score = to_score(
                match.get("home_score")
            )

            opponent_score = to_score(
                match.get("away_score")
            )

        # ====================================================
        # DEPLASMAN
        # ====================================================

        elif away_id == team_id:

            location = "away"

            value = match.get(
                "away_value"
            )

            opponent = match.get(
                "home_team_name"
            )

            opponent_id = home_id

            team_score = to_score(
                match.get("away_score")
            )

            opponent_score = to_score(
                match.get("home_score")
            )

        else:

            continue

        # ====================================================
        # SONUÇ
        # ====================================================

        match_result = "N/A"

        if (
            team_score is not None
            and opponent_score is not None
        ):

            if team_score > opponent_score:
                match_result = "W"

            elif team_score < opponent_score:
                match_result = "L"

            else:
                match_result = "D"

        # ====================================================
        # TARİH
        # ====================================================

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

        # ====================================================
        # İSTATİSTİK DEĞERİ
        # ====================================================

        numeric_value = to_number(
            value
        )

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

            "result": match_result,

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
# İSTATİSTİKSEL ÖZET
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
# GOL ANALİZİ
# ============================================================

def calculate_goal_analysis(matches):

    goals_for = []
    goals_against = []

    wins = 0
    draws = 0
    losses = 0

    for match in matches:

        team_score = match.get(
            "team_score"
        )

        opponent_score = match.get(
            "opponent_score"
        )

        if (
            team_score is None
            or opponent_score is None
        ):
            continue

        goals_for.append(
            team_score
        )

        goals_against.append(
            opponent_score
        )

        if team_score > opponent_score:
            wins += 1

        elif team_score < opponent_score:
            losses += 1

        else:
            draws += 1

    if not goals_for:

        return {

            "available": False,

            "matches": 0,

            "goals_for": {

                "count": 0,
                "average": None,
                "median": None,
                "minimum": None,
                "maximum": None

            },

            "goals_against": {

                "count": 0,
                "average": None,
                "median": None,
                "minimum": None,
                "maximum": None

            },

            "wins": 0,
            "draws": 0,
            "losses": 0

        }

    return {

        "available": True,

        "matches": len(goals_for),

        "goals_for": {

            "count": len(goals_for),

            "average": round(
                statistics.mean(goals_for),
                4
            ),

            "median": round(
                statistics.median(goals_for),
                4
            ),

            "minimum": min(
                goals_for
            ),

            "maximum": max(
                goals_for
            )

        },

        "goals_against": {

            "count": len(goals_against),

            "average": round(
                statistics.mean(goals_against),
                4
            ),

            "median": round(
                statistics.median(goals_against),
                4
            ),

            "minimum": min(
                goals_against
            ),

            "maximum": max(
                goals_against
            )

        },

        "wins": wins,

        "draws": draws,

        "losses": losses

    }


# ============================================================
# ANA ANALİZ
# ============================================================

analysis = {

    "source": "StatsHub",

    "fixture_id": source.get(
        "fixture_id"
    ),

    "teams": TEAMS,

    "team_analysis": {}

}


# ============================================================
# TAKIMLARI ANALİZ ET
# ============================================================

for team_name, team_id in TEAMS.items():

    print("")
    print(
        "=========================================="
    )
    print(
        team_name
    )
    print(
        "=========================================="
    )

    analysis[
        "team_analysis"
    ][team_name] = {

        "team_id": team_id,

        "goals": {},

        "statistics": {}

    }

    # ========================================================
    # GOAL ANALİZİ
    # ========================================================

    goals_stat_info = source[
        "data"
    ][team_name].get(
        "goals"
    )

    if goals_stat_info:

        goal_matches = extract_team_matches(
            team_name,
            team_id,
            goals_stat_info
        )

        goal_analysis = calculate_goal_analysis(
            goal_matches
        )

        analysis[
            "team_analysis"
        ][team_name][
            "goals"
        ] = goal_analysis

    else:

        analysis[
            "team_analysis"
        ][team_name][
            "goals"
        ] = {
            "available": False
        }

    # ========================================================
    # DİĞER İSTATİSTİKLER
    # ========================================================

    for stat_name, stat_info in source[
        "data"
    ][team_name].items():

        # goals'u burada tekrar işlemiyoruz
        if stat_name == "goals":
            continue

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

        # ====================================================
        # EV
        # ====================================================

        home_matches = [

            m for m in matches

            if m.get(
                "location"
            ) == "home"

        ]

        # ====================================================
        # DEPLASMAN
        # ====================================================

        away_matches = [

            m for m in matches

            if m.get(
                "location"
            ) == "away"

        ]

        home_stats = calculate_statistics(
            home_matches
        )

        away_stats = calculate_statistics(
            away_matches
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

            "home_count":
                home_stats[
                    "count"
                ],

            "home_average":
                home_stats[
                    "average"
                ],

            "home_median":
                home_stats[
                    "median"
                ],

            "away_count":
                away_stats[
                    "count"
                ],

            "away_average":
                away_stats[
                    "average"
                ],

            "away_median":
                away_stats[
                    "median"
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
# GOL EV / DEPLASMAN AYRIMI
# ============================================================

for team_name in TEAMS:

    goal_info = analysis[
        "team_analysis"
    ][team_name][
        "goals"
    ]

    # Goals için gerçek maçları tekrar çıkar
    goals_stat_info = source[
        "data"
    ][team_name].get(
        "goals"
    )

    if not goals_stat_info:
        continue

    goal_matches = extract_team_matches(
        team_name,
        TEAMS[team_name],
        goals_stat_info
    )

    home_matches = [

        m for m in goal_matches

        if m.get(
            "location"
        ) == "home"

    ]

    away_matches = [

        m for m in goal_matches

        if m.get(
            "location"
        ) == "away"

    ]

    # --------------------------------------------------------
    # Gol For
    # --------------------------------------------------------

    home_goals_for = [

        m["team_score"]

        for m in home_matches

        if m["team_score"] is not None

    ]

    away_goals_for = [

        m["team_score"]

        for m in away_matches

        if m["team_score"] is not None

    ]

    # --------------------------------------------------------
    # Gol Against
    # --------------------------------------------------------

    home_goals_against = [

        m["opponent_score"]

        for m in home_matches

        if m["opponent_score"] is not None

    ]

    away_goals_against = [

        m["opponent_score"]

        for m in away_matches

        if m["opponent_score"] is not None

    ]

    def avg(values):

        if not values:
            return None

        return round(
            statistics.mean(values),
            4
        )

    goal_info[
        "home_matches"
    ] = len(home_goals_for)

    goal_info[
        "away_matches"
    ] = len(away_goals_for)

    goal_info[
        "home_goals_for_average"
    ] = avg(
        home_goals_for
    )

    goal_info[
        "away_goals_for_average"
    ] = avg(
        away_goals_for
    )

    goal_info[
        "home_goals_against_average"
    ] = avg(
        home_goals_against
    )

    goal_info[
        "away_goals_against_average"
    ] = avg(
        away_goals_against
    )


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
# KONSOL ÖZETİ
# ============================================================

print("")
print("")
print("==========================================")
print("STATSHUB ANALİZ TAMAMLANDI")
print("==========================================")
print("")

for team_name in TEAMS:

    team_data = analysis[
        "team_analysis"
    ][team_name]

    goals = team_data[
        "goals"
    ]

    print(
        "------------------------------------------"
    )

    print(
        team_name
    )

    print(
        "Gol For ortalama:",
        goals.get(
            "goals_for",
            {}
        ).get(
            "average"
        )
    )

    print(
        "Gol Against ortalama:",
        goals.get(
            "goals_against",
            {}
        ).get(
            "average"
        )
    )

    print(
        "W:",
        goals.get(
            "wins"
        ),
        "D:",
        goals.get(
            "draws"
        ),
        "L:",
        goals.get(
            "losses"
        )
    )

    print(
        "Toplam istatistik:",
        len(
            team_data[
                "statistics"
            ]
        )
    )

print("")
print(
    "Çıktı:"
)
print(
    OUTPUT_FILE
)
print("")
