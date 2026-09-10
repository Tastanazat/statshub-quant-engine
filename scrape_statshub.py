from playwright.sync_api import sync_playwright
import json
import os
import re
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

js_hits = []
api_hits = []

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    # -------------------------------------------------------
    # RESPONSE YAKALAMA
    # -------------------------------------------------------

    def response_handler(response):

        try:
            url = response.url

            if "/api/" in url:
                api_hits.append({
                    "status": response.status,
                    "url": url,
                    "method": response.request.method
                })

        except Exception:
            pass

    page.on("response", response_handler)

    # -------------------------------------------------------
    # SAYFAYI AÇ
    # -------------------------------------------------------

    print("StatsHub açılıyor...")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    time.sleep(5)

    print("Sayfa yüklendi.")

    # -------------------------------------------------------
    # SAYFADAKİ TÜM SCRIPT URL'LERİNİ AL
    # -------------------------------------------------------

    scripts = page.locator("script[src]")

    script_urls = []

    for i in range(scripts.count()):

        try:

            src = scripts.nth(i).get_attribute("src")

            if src:
                script_urls.append(src)

        except Exception:
            pass

    print(
        "Script sayısı:",
        len(script_urls)
    )

    # -------------------------------------------------------
    # JS DOSYALARINI OKU
    # -------------------------------------------------------

    for i, script_url in enumerate(
        script_urls,
        start=1
    ):

        try:

            if script_url.startswith("/"):
                full_url = (
                    "https://www.statshub.com"
                    + script_url
                )
            else:
                full_url = script_url

            response = page.request.get(
                full_url,
                timeout=60000
            )

            if response.status != 200:
                continue

            text = response.text()

            # ------------------------------------------------
            # TEAM EVENT-STATISTICS İFADELERİNİ BUL
            # ------------------------------------------------

            if (
                "event-statistics" in text
                or "statisticKey" in text
                or "possession" in text.lower()
                or "corners" in text.lower()
                or "tackles" in text.lower()
                or "crosses" in text.lower()
            ):

                js_hits.append({
                    "script": full_url,
                    "length": len(text)
                })

                # --------------------------------------------
                # event-statistics çevresindeki parçaları al
                # --------------------------------------------

                for match in re.finditer(
                    r"event-statistics",
                    text,
                    re.IGNORECASE
                ):

                    start = max(
                        0,
                        match.start() - 1500
                    )

                    end = min(
                        len(text),
                        match.end() + 3000
                    )

                    snippet = text[start:end]

                    js_hits[-1].setdefault(
                        "snippets",
                        []
                    ).append(snippet)

        except Exception:
            continue

    # -------------------------------------------------------
    # TEAM STATS SAYFASINA TIKLA
    # -------------------------------------------------------

    try:

        team_stats = page.get_by_text(
            "Team Stats",
            exact=True
        ).first

        team_stats.click(
            timeout=10000
        )

        time.sleep(4)

        print(
            "Team Stats açıldı."
        )

    except Exception as e:

        print(
            "Team Stats tıklanamadı:",
            str(e)
        )

    # -------------------------------------------------------
    # SAYFADAKİ TÜM METNİ KAYDET
    # -------------------------------------------------------

    try:

        page_text = page.locator(
            "body"
        ).inner_text()

        with open(
            "data/statshub_team_stats_page.txt",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(page_text)

    except Exception:
        pass

    browser.close()


# ============================================================
# API URL'LERİNİ TEMİZLE
# ============================================================

unique_api = []

seen = set()

for item in api_hits:

    url = item["url"]

    if url not in seen:

        seen.add(url)
        unique_api.append(item)


# ============================================================
# SONUÇLARI KAYDET
# ============================================================

with open(
    "data/statshub_js_discovery.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        js_hits,
        f,
        ensure_ascii=False,
        indent=2
    )


with open(
    "data/statshub_api_capture.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        unique_api,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# URL LİSTESİ
# ============================================================

with open(
    "data/statshub_api_urls.txt",
    "w",
    encoding="utf-8"
) as f:

    for item in unique_api:

        f.write(
            f'{item["status"]} | {item["url"]}\n'
        )


print("")
print("==========================================")
print("STATSHUB JS KEŞİF TAMAMLANDI")
print("==========================================")
print("")
print(
    "API çağrısı:",
    len(unique_api)
)
print(
    "İlgili JS dosyası:",
    len(js_hits)
)
print("")
print("Oluşturulan dosyalar:")
print("")
print("statshub_js_discovery.json")
print("statshub_api_capture.json")
print("statshub_api_urls.txt")
print("statshub_team_stats_page.txt")
print("")
