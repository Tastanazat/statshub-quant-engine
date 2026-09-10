from playwright.sync_api import sync_playwright
import requests
import json
import os
from urllib.parse import urlparse


# ============================================================
# STATSHUB CONFIG
# ============================================================

BASE = "https://www.statshub.com"

FIXTURE_URL = (
    "https://www.statshub.com/fixture/"
    "psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

EVENT_ID = 16938896
FIXTURE_ID = 416477

TEAMS = {
    "PSV": 2952,
    "Shakhtar": 3313,
}

TOURNAMENTS = "7,37,330,340,679,17015"

os.makedirs("data", exist_ok=True)


# ============================================================
# 1. PLAYER PERFORMANCE API
# ============================================================

player_results = {}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
}

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

        print(f"{team_name} HTTP:", response.status_code)

        try:
            data = response.json()
        except Exception:
            data = {
                "raw_text": response.text
            }

        player_results[team_name] = {
            "team_id": team_id,
            "url": url,
            "status_code": response.status_code,
            "data": data,
        }

    except Exception as e:

        player_results[team_name] = {
            "team_id": team_id,
            "url": url,
            "error": str(e),
        }


with open(
    "data/statshub_players.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        player_results,
        f,
        ensure_ascii=False,
        indent=2
    )


print("Player Stats kaydedildi.")


# ============================================================
# 2. BROWSER NETWORK SCANNER
# ============================================================

network_results = []


def handle_response(response):

    try:

        request = response.request

        if request.resource_type not in ("xhr", "fetch"):
            return

        url = response.url

        # Sadece StatsHub istekleri
        if "statshub.com" not in url:
            return

        item = {
            "url": url,
            "status": response.status,
            "method": request.method,
            "resource_type": request.resource_type,
            "content_type": response.headers.get(
                "content-type",
                ""
            ),
        }

        # API cevaplarını mümkün olduğunca kaydet
        if "/api/" in url:

            try:
                body = response.text()

                item["body"] = body[:50000]

            except Exception as e:

                item["body_error"] = str(e)

        network_results.append(item)

        print(
            "NETWORK:",
            response.status,
            request.resource_type,
            url
        )

    except Exception as e:

        print("Network kayıt hatası:", e)


# ============================================================
# 3. PLAYWRIGHT
# ============================================================

print("")
print("======================================")
print("StatsHub browser taraması başlıyor...")
print("======================================")
print("")


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        viewport={
            "width": 1440,
            "height": 1000
        }
    )

    page.on(
        "response",
        handle_response
    )

    # --------------------------------------------------------
    # Fixture aç
    # --------------------------------------------------------

    print("Fixture açılıyor...")

    page.goto(
        FIXTURE_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(7000)


    # --------------------------------------------------------
    # Player Stats
    # --------------------------------------------------------

    print("")
    print("PLAYER STATS taranıyor...")

    try:

        tab = page.get_by_text(
            "Player Stats",
            exact=True
        ).first

        if tab.is_visible():

            tab.click(
                timeout=10000
            )

            page.wait_for_timeout(6000)

            print("Player Stats açıldı.")

    except Exception as e:

        print(
            "Player Stats tıklama:",
            e
        )


    # --------------------------------------------------------
    # Team Stats
    # --------------------------------------------------------

    print("")
    print("TEAM STATS taranıyor...")

    try:

        tab = page.get_by_text(
            "Team Stats",
            exact=True
        ).first

        if tab.is_visible():

            tab.click(
                timeout=10000
            )

            page.wait_for_timeout(8000)

            print("Team Stats açıldı.")

    except Exception as e:

        print(
            "Team Stats tıklama:",
            e
        )


    # --------------------------------------------------------
    # Lineups
    # --------------------------------------------------------

    print("")
    print("LINEUPS taranıyor...")

    try:

        tab = page.get_by_text(
            "Lineups",
            exact=True
        ).first

        if tab.is_visible():

            tab.click(
                timeout=10000
            )

            page.wait_for_timeout(6000)

            print("Lineups açıldı.")

    except Exception as e:

        print(
            "Lineups tıklama:",
            e
        )


    # --------------------------------------------------------
    # Team Stats tekrar
    # --------------------------------------------------------

    print("")
    print("TEAM STATS ikinci tarama...")

    try:

        tab = page.get_by_text(
            "Team Stats",
            exact=True
        ).first

        if tab.is_visible():

            tab.click(
                timeout=10000
            )

            page.wait_for_timeout(5000)

    except Exception:
        pass


    # --------------------------------------------------------
    # Render edilmiş sayfayı kaydet
    # --------------------------------------------------------

    html = page.content()

    text = page.locator(
        "body"
    ).inner_text()


    with open(
        "data/statshub_rendered.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)


    with open(
        "data/statshub_text.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)


    browser.close()


# ============================================================
# 4. NETWORK SONUÇLARINI KAYDET
# ============================================================

with open(
    "data/statshub_network.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        network_results,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# 5. API ADRESLERİNİ AYIKLA
# ============================================================

api_urls = []

for item in network_results:

    url = item.get("url", "")

    if "/api/" in url:

        if url not in api_urls:

            api_urls.append(url)


with open(
    "data/statshub_api_urls.txt",
    "w",
    encoding="utf-8"
) as f:

    for url in api_urls:

        f.write(url)
        f.write("\n")


# ============================================================
# 6. ÖZET
# ============================================================

print("")
print("======================================")
print("TARAMA TAMAMLANDI")
print("======================================")

print(
    "Toplam network kaydı:",
    len(network_results)
)

print(
    "API adresi:",
    len(api_urls)
)

print("")
print("Bulunan API adresleri:")
print("")

for i, url in enumerate(
    api_urls,
    start=1
):

    print(
        f"{i}. {url}"
    )

print("")
print("Dosyalar:")
print("data/statshub_players.json")
print("data/statshub_network.json")
print("data/statshub_api_urls.txt")
print("data/statshub_rendered.html")
print("data/statshub_text.txt")
