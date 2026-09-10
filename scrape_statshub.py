import requests
import json
import os
import time

# ============================================================
# STATSHUB TEAM STATS DATA ENGINE
# ============================================================

BASE_URL = "https://www.statshub.com"

TEAMS = {
    "PSV": 2952,
    "Shakhtar": 3313
}

TOURNAMENT_IDS = "7,37,330,340,679,17015"

FIXTURE_ID = 16938896

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*"
}

# ============================================================
# GERÇEK STATSHUB STATISTIC KEY'LERİ
# ============================================================

STATISTICS = {

    "goals": "goals",

    "corners": "cornerKicks",

    "shots": "totalShotsOnGoal",

    "crosses": "accurateCross",

    "tackles": "totalTackle",

    "possession": "ballPossession",

    "cards": "cards",

    "bigChanceCreated": "bigChanceCreated",

    "bigChanceMissed": "bigChanceMissed",

    "bigChanceScored": "bigChanceScored",

    "expectedGoals": "expectedGoals",

    "shotsOnGoal": "shotsOnGoal",

    "shotsOffGoal": "shotsOffGoal",

    "totalShotsInsideBox": "totalShotsInsideBox",

    "totalShotsOutsideBox": "totalShotsOutsideBox",

    "totalClearance": "totalClearance",

    "dispossessed": "dispossessed",

    "errorsLeadToGoal": "errorsLeadToGoal",

    "errorsLeadToShot": "errorsLeadToShot",

    "fouls": "fouls",

    "goalkeeperSaves": "goalkeeperSaves",

    "interceptionWon": "interceptionWon",

    "freeKicks": "freeKicks",

    "goalKicks": "goalKicks",

    "throwIns": "throwIns",

    "offsides": "offsides",

    "passes": "passes",

    "touchesInOppBox": "touchesInOppBox",

    "redCards": "redCards",

    "yellowCards": "yellowCards",

}


# ============================================================
# KLASÖR
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)


# ============================================================
# TEK İSTATİSTİK ÇEKME
# ============================================================

def fetch_stat(
    team_id,
    stat_key
):

    url = (
        f"{BASE_URL}/api/team/{team_id}/event-statistics"
        f"?eventType=all"
        f"&statisticKey={stat_key}"
        f"&eventHalf=ALL"
        f"&tournamentIds={TOURNAMENT_IDS}"
        f"&limit=20"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        status = response.status_code

        try:
            data = response.json()
        except Exception:
            data = None

        # ----------------------------------------------------
        # DATA KONTROL
        # ----------------------------------------------------

        records = []

        if isinstance(data, list):

            records = data

        elif isinstance(data, dict):

            if isinstance(
                data.get("data"),
                list
            ):

                records = data["data"]

            elif isinstance(
                data.get("result"),
                list
            ):

                records = data["result"]

        return {
            "url": url,
            "status_code": status,
            "record_count": len(records),
            "available": (
                status == 200
                and len(records) > 0
            ),
            "data": data
        }

    except Exception as e:

        return {
            "url": url,
            "status_code": None,
            "record_count": 0,
            "available": False,
            "error": str(e),
            "data": None
        }


# ============================================================
# TÜM VERİYİ TOPLA
# ============================================================

dataset = {

    "source": "StatsHub",

    "fixture_id": FIXTURE_ID,

    "teams": TEAMS,

    "tournament_ids": TOURNAMENT_IDS,

    "statistics": STATISTICS,

    "data": {}

}


# ============================================================
# TAKIMLAR
# ============================================================

for team_name, team_id in TEAMS.items():

    print("")
    print("==========================================")
    print(team_name)
    print("Team ID:", team_id)
    print("==========================================")

    dataset["data"][team_name] = {}

    for stat_name, stat_key in STATISTICS.items():

        print(
            f"{stat_name} -> {stat_key}",
            end=" : "
        )

        result = fetch_stat(
            team_id,
            stat_key
        )

        dataset["data"][team_name][
            stat_name
        ] = {

            "statistic_key": stat_key,

            "url": result["url"],

            "status_code": result[
                "status_code"
            ],

            "record_count": result[
                "record_count"
            ],

            "available": result[
                "available"
            ],

            "data": result[
                "data"
            ]
        }

        if result["available"]:

            print(
                "OK",
                result["record_count"],
                "kayıt"
            )

        else:

            print(
                "N/A"
            )

        time.sleep(0.15)


# ============================================================
# ANA JSON
# ============================================================

with open(
    "data/statshub_team_stats.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        dataset,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# ÖZET
# ============================================================

summary = {

    "source": "StatsHub",

    "fixture_id": FIXTURE_ID,

    "teams": list(
        TEAMS.keys()
    ),

    "statistics": {},

}


for stat_name, stat_key in STATISTICS.items():

    summary["statistics"][
        stat_name
    ] = {

        "statistic_key": stat_key,

        "PSV": dataset["data"]["PSV"][
            stat_name
        ]["available"],

        "Shakhtar": dataset["data"]["Shakhtar"][
            stat_name
        ]["available"],

        "PSV_records": dataset["data"]["PSV"][
            stat_name
        ]["record_count"],

        "Shakhtar_records": dataset["data"]["Shakhtar"][
            stat_name
        ]["record_count"]

    }


with open(
    "data/statshub_team_stats_summary.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# OK / N/A LİSTESİ
# ============================================================

with open(
    "data/statshub_team_stats_status.txt",
    "w",
    encoding="utf-8"
) as f:

    for stat_name, stat_key in STATISTICS.items():

        psv = dataset["data"]["PSV"][
            stat_name
        ]

        sha = dataset["data"]["Shakhtar"][
            stat_name
        ]

        f.write(
            f"{stat_name} | "
            f"{stat_key} | "
            f"PSV={psv['record_count']} | "
            f"Shakhtar={sha['record_count']} | "
            f"PSV_OK={psv['available']} | "
            f"Shakhtar_OK={sha['available']}\n"
        )


# ============================================================
# SONUÇ
# ============================================================

print("")
print("")
print("==========================================")
print("STATSHUB TEAM STATS ENGINE TAMAMLANDI")
print("==========================================")
print("")

print(
    "Toplam istatistik:",
    len(STATISTICS)
)

print("")

for stat_name, stat_key in STATISTICS.items():

    psv_count = dataset["data"]["PSV"][
        stat_name
    ]["record_count"]

    sha_count = dataset["data"]["Shakhtar"][
        stat_name
    ]["record_count"]

    print(
        f"{stat_name:30} "
        f"PSV={psv_count:2} "
        f"Shakhtar={sha_count:2}"
    )

print("")
print("JSON:")
print("data/statshub_team_stats.json")
print("")
