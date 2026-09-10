from playwright.sync_api import sync_playwright
import os
import json
import re
import time

URL = "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"

os.makedirs("data/statshub_js", exist_ok=True)

TARGETS = [
    "corners",
    "shots",
    "crosses",
    "tackles",
    "possession",
]

all_scripts = []
relevant_scripts = []

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    print("StatsHub açılıyor...")

    page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=120000
    )

    time.sleep(8)

    print("Sayfa yüklendi.")

    # ========================================================
    # SAYFADAKİ SCRIPT URL'LERİNİ TOPLA
    # ========================================================

    script_locators = page.locator("script[src]")

    count = script_locators.count()

    print("Bulunan script:", count)

    for i in range(count):

        try:

            src = script_locators.nth(i).get_attribute("src")

            if src and "_next/static" in src:

                if src.startswith("/"):
                    src = "https://www.statshub.com" + src

                if src not in all_scripts:
                    all_scripts.append(src)

        except Exception:
            pass

    print(
        "Next.js script:",
        len(all_scripts)
    )

    # ========================================================
    # HER JS DOSYASINI KAYDET
    # ========================================================

    for index, script_url in enumerate(
        all_scripts,
        start=1
    ):

        try:

            print(
                f"[{index}/{len(all_scripts)}] JS indiriliyor..."
            )

            response = page.request.get(
                script_url,
                timeout=60000
            )

            if response.status != 200:
                continue

            text = response.text()

            # güvenli dosya adı
            filename = (
                f"{index:03d}_"
                + script_url.split("/")[-1]
            )

            filepath = os.path.join(
                "data/statshub_js",
                filename
            )

            with open(
                filepath,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(text)

            # =================================================
            # HEDEF KELİMELERİ İÇEREN JS'LERİ BELİRLE
            # =================================================

            lower_text = text.lower()

            found_targets = []

            for target in TARGETS:

                if target.lower() in lower_text:

                    found_targets.append(
                        target
                    )

            if (
                found_targets
                or "statistickey" in lower_text
                or "event-statistics" in lower_text
            ):

                relevant_scripts.append({
                    "url": script_url,
                    "file": filepath,
                    "length": len(text),
                    "targets": found_targets,
                    "has_statisticKey": (
                        "statistickey" in lower_text
                    ),
                    "has_event_statistics": (
                        "event-statistics"
                        in lower_text
                    )
                })

        except Exception as e:

            print(
                "JS hata:",
                str(e)
            )

    # ========================================================
    # SAYFA HTML'İNİ DE KAYDET
    # ========================================================

    try:

        html = page.content()

        with open(
            "data/statshub_page.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

    except Exception:
        pass

    browser.close()


# ============================================================
# İLGİLİ JS LİSTESİ
# ============================================================

with open(
    "data/statshub_relevant_js.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        relevant_scripts,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# HEDEF KELİMELERİ VE ÇEVRESİNİ ÇIKAR
# ============================================================

snippets = []

for item in relevant_scripts:

    try:

        with open(
            item["file"],
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

        lower_text = text.lower()

        for target in TARGETS:

            start_pos = 0

            while True:

                pos = lower_text.find(
                    target.lower(),
                    start_pos
                )

                if pos == -1:
                    break

                start = max(
                    0,
                    pos - 1200
                )

                end = min(
                    len(text),
                    pos + 2500
                )

                snippets.append({
                    "target": target,
                    "file": item["file"],
                    "script_url": item["url"],
                    "snippet": text[start:end]
                })

                start_pos = pos + len(target)

    except Exception:
        pass


# ============================================================
# SNIPPET DOSYASI
# ============================================================

with open(
    "data/statshub_target_snippets.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        snippets,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# ÖZET
# ============================================================

summary = {
    "source": "StatsHub",
    "fixture": URL,
    "total_next_scripts": len(all_scripts),
    "relevant_scripts": len(relevant_scripts),
    "target_snippets": len(snippets),
    "targets": TARGETS
}

with open(
    "data/statshub_js_summary.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        ensure_ascii=False,
        indent=2
    )


print("")
print("==========================================")
print("STATSHUB JS TAM TARAMA TAMAMLANDI")
print("==========================================")
print("")
print(
    "Toplam JS:",
    len(all_scripts)
)
print(
    "İlgili JS:",
    len(relevant_scripts)
)
print(
    "Bulunan hedef snippet:",
    len(snippets)
)
print("")
print("Hedefler:")
print("CORNERS")
print("SHOTS")
print("CROSSES")
print("TACKLES")
print("POSSESSION")
print("")
print("Dosyalar:")
print("data/statshub_js/")
print("data/statshub_relevant_js.json")
print("data/statshub_target_snippets.json")
print("data/statshub_js_summary.json")
print("")
