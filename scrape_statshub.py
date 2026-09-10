from playwright.sync_api import sync_playwright
import json
import os
import time

URL = "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"

TARGETS = [
    "CORNERS",
    "SHOTS",
    "CROSSES",
    "TACKLES",
    "POSSESSION",
]

os.makedirs("data", exist_ok=True)

captured = []

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    # =====================================================
    # TÜM API İSTEKLERİNİ YAKALA
    # =====================================================

    def handle_response(response):

        try:
            url = response.url

            if "/api/" not in url:
                return

            record = {
                "status": response.status,
                "url": url,
                "method": response.request.method,
            }

            if (
                "/event-statistics" in url
                or "/team/" in url
            ):
                try:
                    record["body"] = response.json()
                except Exception:
                    record["body"] = None

            captured.append(record)

        except Exception:
            pass

    page.on(
        "response",
        handle_response
    )

    print("StatsHub açılıyor...")

    page.goto(
        URL,
        wait_until="networkidle",
        timeout=120000
    )

    time.sleep(3)

    # =====================================================
    # TEAM STATS'A GİT
    # =====================================================

    print("Team Stats aranıyor...")

    try:

        team_stats = page.get_by_text(
            "Team Stats",
            exact=True
        ).first

        team_stats.click(
            timeout=10000
        )

        time.sleep(3)

    except Exception as e:

        print(
            "Team Stats tıklama hatası:",
            e
        )

    # =====================================================
    # HER KATEGORİYİ TEK TEK TIKLA
    # =====================================================

    for target in TARGETS:

        print("")
        print(
            "================================"
        )
        print(
            "TEST:",
            target
        )
        print(
            "================================"
        )

        before = len(captured)

        try:

            locator = page.get_by_text(
                target,
                exact=True
            ).first

            locator.click(
                timeout=5000,
                force=True
            )

            print(
                target,
                "tıklandı."
            )

            # API çağrısının oluşmasını bekle
            time.sleep(2)

        except Exception as e:

            print(
                target,
                "tıklanamadı:",
                e
            )

        # Bu tıklamadan sonra gelen yeni API'leri göster
        new_items = captured[before:]

        for item in new_items:

            if (
                "/event-statistics" in
                item["url"]
            ):

                print("")
                print(
                    "YAKALANDI:"
                )

                print(
                    item["status"]
                )

                print(
                    item["url"]
                )

    browser.close()


# ============================================================
# SADECE EVENT-STATISTICS İSTEKLERİNİ AYIR
# ============================================================

event_stats = []

for item in captured:

    if "/event-statistics" in item["url"]:

        event_stats.append(item)


# ============================================================
# KAYDET
# ============================================================

with open(
    "data/statshub_missing_stats_network.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        event_stats,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# URL LİSTESİ
# ============================================================

with open(
    "data/statshub_missing_stats_urls.txt",
    "w",
    encoding="utf-8"
) as f:

    for item in event_stats:

        f.write(
            f'{item["status"]} | {item["url"]}\n'
        )


print("")
print("")
print("==========================================")
print("TARAMA TAMAMLANDI")
print("==========================================")
print("")
print(
    "Yakalanan event-statistics:",
    len(event_stats)
)
print("")
print(
    "Sonuç:",
    "data/statshub_missing_stats_network.json"
)
print("")
