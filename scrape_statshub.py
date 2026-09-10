import requests
import json
import os
import time

# ============================================================
# STATSHUB TEAM STATS API DISCOVERY
# ============================================================

BASE = "https://www.statshub.com"

TEAMS = {
    "PSV": 2952,
    "Shakhtar": 3313,
}

TOURNAMENT_IDS = "7,37,330,340,679,17015"

os.makedirs("data", exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
}

# ============================================================
# STATSHUB'DA GÖRÜNEN TEAM STATISTICS ANAHTARLARI
# ============================================================

STAT_KEYS = [
    "goals",
    "corners",
    "shots",
    "cards",
    "crosses",
    "bigChanceCreated",
    "bigChanceMissed",
    "bigChanceScored",
    "expectedGoals",
    "shotsOnGoal",
    "shotsOffGoal",
    "totalShotsInsideBox",
    "totalShotsOutsideBox",
    "totalClearance",
    "dispossessed",
    "errorsLeadToGoal",
    "errorsLeadToShot",
    "fouls",
    "goalkeeperSaves",
    "interceptionWon",
    "tackles",
    "freeKicks",
    "goalKicks",
    "throwIns",
    "possession",
    "offsides",
    "passes",
    "touchesInOppBox",
    "redCards",
    "yellowCards",
]

# ============================================================
# SONUÇLAR
# ============================================================

results = {}

valid_keys = []

print("")
print("==========================================")
print("STATSHUB TEAM STATS API TESTİ")
print("==========================================")
print("")

# ============================================================
# HER TAKIM + HER İSTATİSTİK
# ============================================================

for team_name, team_id in TEAMS.items():

    print("")
    print("------------------------------------------")
    print(team_name, "TEAM ID:", team_id)
    print("------------------------------------------")

    results[team_name] = {}

    for stat_key in STAT_KEYS:

        url = (
            f"{BASE}/api/team/{team_id}/event-statistics"
            f"?eventType=all"
            f"&statisticKey={stat_key}"
            f"&eventHalf=ALL"
            f"&tournamentIds={TOURNAMENT_IDS}"
            f"&limit=20"
        )

        print(
            f"{team_name} | {stat_key} ...",
            end=" "
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
                data = {
                    "raw_text": response.text[:10000]
                }

            # ------------------------------------------------
            # Veri kontrolü
            # ------------------------------------------------

            has_data = False
            data_count = 0

            if isinstance(data, dict):

                raw_data = data.get("data")

                if isinstance(raw_data, list):

                    data_count = len(raw_data)

                    if data_count > 0:
                        has_data = True

                elif isinstance(raw_data, dict):

                    has_data = len(raw_data) > 0

                    data_count = len(raw_data)

            elif isinstance(data, list):

                data_count = len(data)

                if data_count > 0:
                    has_data = True

            # ------------------------------------------------
            # Sonucu kaydet
            # ------------------------------------------------

            results[team_name][stat_key] = {
                "url": url,
                "status_code": status,
                "has_data": has_data,
                "data_count": data_count,
                "data": data,
            }

            if status == 200 and has_data:

                print(
                    "OK",
                    f"({data_count} kayıt)"
                )

                if stat_key not in valid_keys:
                    valid_keys.append(stat_key)

            elif status == 200:

                print(
                    "200 - BOŞ"
                )

            else:

                print(
                    f"HTTP {status}"
                )

        except Exception as e:

            print(
                "HATA:",
                str(e)
            )

            results[team_name][stat_key] = {
                "url": url,
                "error": str(e),
            }

        # StatsHub'ı gereksiz yere hızlı sorgulamamak için
        time.sleep(0.15)


# ============================================================
# TÜM SONUÇLARI KAYDET
# ============================================================

with open(
    "data/statshub_team_statistics_probe.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# GEÇERLİ ANAHTARLAR
# ============================================================

with open(
    "data/statshub_valid_team_stats.txt",
    "w",
    encoding="utf-8"
) as f:

    for key in valid_keys:

        f.write(key)
        f.write("\n")


# ============================================================
# ÖZET JSON
# ============================================================

summary = {
    "source": "StatsHub",
    "teams": TEAMS,
    "tournament_ids": TOURNAMENT_IDS,
    "tested_keys": STAT_KEYS,
    "valid_keys": valid_keys,
    "valid_key_count": len(valid_keys),
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
# EKRAN ÖZETİ
# ============================================================

print("")
print("")
print("==========================================")
print("TARAMA TAMAMLANDI")
print("==========================================")
print("")

print(
    "Test edilen istatistik:",
    len(STAT_KEYS)
)

print(
    "Gerçek veri döndüren:",
    len(valid_keys)
)

print("")
print("GEÇERLİ STATSHUB TEAM STATS KEY'LERİ:")
print("")

for i, key in enumerate(
    valid_keys,
    start=1
):

    print(
        f"{i}. {key}"
    )

print("")
print("Dosyalar oluşturuldu:")
print("")
print("1. statshub_team_statistics_probe.json")
print("2. statshub_valid_team_stats.txt")
print("3. statshub_team_stats_summary.json")
print("")
