from playwright.sync_api import sync_playwright
import json
import os

URL = "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"

os.makedirs("data", exist_ok=True)

responses = []

def handle_response(response):
    request = response.request

    if request.resource_type in ("xhr", "fetch"):
        url = response.url

        if "statshub.com" in url:
            item = {
                "url": url,
                "status": response.status,
                "method": request.method,
                "resource_type": request.resource_type,
                "content_type": response.headers.get("content-type", "")
            }

            if "/api/" in url:
                try:
                    item["body"] = response.text()[:30000]
                except Exception:
                    item["body"] = ""

            responses.append(item)


with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    page.on("response", handle_response)

    print("StatsHub açılıyor...")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    page.wait_for_timeout(5000)

    try:
        player_stats = page.get_by_text(
            "Player Stats",
            exact=True
        ).first

        player_stats.click(timeout=5000)

        page.wait_for_timeout(5000)

    except Exception:
        pass

    html = page.content()

    text = page.locator("body").inner_text()

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

    with open(
        "data/network.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            responses,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("Tarama tamamlandı.")
    print("Network kayıtları:", len(responses))

    browser.close()
