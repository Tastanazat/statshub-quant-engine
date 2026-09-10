import requests
import json
import os

os.makedirs("data", exist_ok=True)

BASE = "https://www.statshub.com"

EVENT_ID = 16938896
FIXTURE_ID = 416477

TEAMS = {
    "PSV": 2952,
    "Shakhtar": 3313
}

TOURNAMENTS = "7,37,330,340,679,17015"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*"
}

results = {}

for team_name, team_id in TEAMS.items():

    url = (
        f"{BASE}/api/team/{team_id}/players/performance"
        f"?tournamentId={TOURNAMENTS}"
        f"&limit=20"
        f"&location=both"
        f"&fixtureId={EVENT_ID}"
    )

    print(f"{team_name} verisi çekiliyor...")

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            team_name,
            "HTTP:",
            response.status_code
        )

        try:
            data = response.json()
        except Exception:
            data = {
                "raw_text": response.text
            }

        results[team_name] = {
            "team_id": team_id,
            "url": url,
            "status_code": response.status_code,
            "data": data
        }

    except Exception as e:

        results[team_name] = {
            "team_id": team_id,
            "url": url,
            "error": str(e)
        }


with open(
    "data/statshub_players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        ensure_ascii=False,
        indent=2
    )


print("================================")
print("StatsHub API testi tamamlandı.")
print("================================")
