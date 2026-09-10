import streamlit as st
import requests
import re
from urllib.parse import urljoin

st.set_page_config(
    page_title="StatsHub API Finder",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 StatsHub Veri Kaynağı Bulucu")

st.info(
    "Bu araç yalnızca StatsHub sayfasını inceler. "
    "Amaç, maç istatistiklerinin hangi JavaScript/veri endpointinden geldiğini bulmaktır."
)

url = st.text_input(
    "StatsHub maç URL'si:",
    value="https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🚀 VERİ KAYNAĞINI ARA", type="primary"):

    if not url:
        st.warning("Önce StatsHub URL'si gir.")
        st.stop()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Mobile Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    # ==========================================================
    # 1. SAYFAYI ÇEK
    # ==========================================================

    st.subheader("1️⃣ StatsHub sayfası")

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        html = response.text

        st.success(f"HTTP Status: {response.status_code}")
        st.write(f"HTML uzunluğu: **{len(html):,} karakter**")

    except Exception as e:
        st.error(f"Sayfa alınamadı: {e}")
        st.stop()

    # ==========================================================
    # 2. JAVASCRIPT DOSYALARINI BUL
    # ==========================================================

    st.subheader("2️⃣ JavaScript dosyaları")

    script_urls = []

    patterns = [
        r'<script[^>]+src=["\']([^"\']+)["\']',
        r'<script[^>]+src=([^ >]+)'
    ]

    for pattern in patterns:
        matches = re.findall(
            pattern,
            html,
            flags=re.IGNORECASE
        )

        for item in matches:

            item = item.strip('"\' ')

            full_url = urljoin(url, item)

            if full_url not in script_urls:
                script_urls.append(full_url)

    st.write(f"Bulunan JavaScript dosyası: **{len(script_urls)}**")

    # ==========================================================
    # 3. JS DOSYALARINI İNDİR
    # ==========================================================

    st.subheader("3️⃣ JavaScript taraması")

    all_js = []

    progress = st.progress(0)

    for i, js_url in enumerate(script_urls):

        try:

            r = requests.get(
                js_url,
                headers=headers,
                timeout=20
            )

            if r.status_code == 200:

                all_js.append({
                    "url": js_url,
                    "text": r.text
                })

        except:
            pass

        progress.progress(
            int((i + 1) / max(len(script_urls), 1) * 100)
        )

    st.success(
        f"{len(all_js)} JavaScript dosyası başarıyla indirildi."
    )

    # ==========================================================
    # 4. GERÇEK NETWORK ÇAĞRILARINI ARA
    # ==========================================================

    st.subheader("4️⃣ Olası API / Network çağrıları")

    network_patterns = {

        "fetch": r'fetch\s*\(',

        "axios": r'axios(?:\.[a-zA-Z]+)?\s*\(',

        "XMLHttpRequest": r'XMLHttpRequest',

        "graphql": r'graphql',

        "/api/": r'["\'][^"\']*/api/[^"\']*["\']',

        "api.": r'["\'][^"\']*api\.[^"\']*["\']',

        "baseURL": r'baseURL',

        "eventId": r'eventId',

        "homeTeamId": r'homeTeamId',

        "awayTeamId": r'awayTeamId',

        "playerStats": r'playerStats',

        "teamStats": r'teamStats',

        "lineups": r'lineups',

        "statistics": r'statistics',

        "matchStats": r'matchStats'
    }

    results = []

    for js in all_js:

        text = js["text"]
        js_url = js["url"]

        for name, pattern in network_patterns.items():

            matches = list(
                re.finditer(
                    pattern,
                    text,
                    flags=re.IGNORECASE
                )
            )

            for match in matches[:20]:

                start = max(
                    0,
                    match.start() - 250
                )

                end = min(
                    len(text),
                    match.end() + 500
                )

                snippet = text[start:end]

                results.append({
                    "type": name,
                    "url": js_url,
                    "snippet": snippet
                })

    st.write(
        f"Toplam potansiyel network/API bölgesi: **{len(results)}**"
    )

    # ==========================================================
    # 5. SADECE GERÇEK STRING URL'LERİ ÇIKAR
    # ==========================================================

    st.subheader("5️⃣ Bulunan URL / endpoint adayları")

    endpoint_candidates = set()

    url_patterns = [

        r'["\'](https?://[^"\']+)["\']',

        r'["\']([^"\']*/api/[^"\']*)["\']',

        r'["\']([^"\']*graphql[^"\']*)["\']',

        r'["\']([^"\']*statistics[^"\']*)["\']',

        r'["\']([^"\']*lineup[^"\']*)["\']',

        r'["\']([^"\']*player[^"\']*)["\']',

        r'["\']([^"\']*team[^"\']*)["\']',

        r'["\']([^"\']*event[^"\']*)["\']'
    ]

    for js in all_js:

        text = js["text"]

        for pattern in url_patterns:

            matches = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )

            for value in matches:

                value = value.strip()

                # Çok kısa veya CSS/font vb. değerleri at
                if len(value) < 5:
                    continue

                if value.startswith("data:"):
                    continue

                if "font" in value.lower():
                    continue

                if "stylesheet" in value.lower():
                    continue

                if "google" in value.lower():
                    continue

                endpoint_candidates.add(value)

    candidates = sorted(endpoint_candidates)

    st.write(
        f"Filtrelenmiş aday sayısı: **{len(candidates)}**"
    )

    if candidates:

        for i, candidate in enumerate(candidates[:100], 1):

            st.code(
                f"{i}. {candidate}",
                language="text"
            )

    else:

        st.warning(
            "Henüz doğrudan endpoint bulunamadı."
        )

    # ==========================================================
    # 6. ÖNEMLİ KOD BÖLGELERİ
    # ==========================================================

    st.subheader("6️⃣ StatsHub maç verisiyle ilgili kod bölgeleri")

    important_words = [
        "showMatchStats",
        "homeTeamPlayer",
        "playerStats",
        "teamStats",
        "matchStats",
        "eventId",
        "homeTeamId",
        "awayTeamId",
        "lineups",
        "statistics"
    ]

    important_results = []

    for js in all_js:

        text = js["text"]

        for word in important_words:

            for match in re.finditer(
                re.escape(word),
                text,
                flags=re.IGNORECASE
            ):

                start = max(
                    0,
                    match.start() - 500
                )

                end = min(
                    len(text),
                    match.end() + 1000
                )

                important_results.append({
                    "word": word,
                    "url": js["url"],
                    "snippet": text[start:end]
                })

    st.write(
        f"Önemli kod bölgesi: **{len(important_results)}**"
    )

    # Sadece ilk 50 göster
    for i, item in enumerate(
        important_results[:50],
        1
    ):

        with st.expander(
            f"#{i} — {item['word']}"
        ):

            st.caption(item["url"])

            st.code(
                item["snippet"],
                language="javascript"
            )

    # ==========================================================
    # 7. ÖZET
    # ==========================================================

    st.divider()

    st.subheader("📌 SONUÇ")

    st.write(
        f"""
        **StatsHub sayfası:** OK

        **HTTP:** {response.status_code}

        **JavaScript dosyası:** {len(script_urls)}

        **Başarıyla indirilen JS:** {len(all_js)}

        **Network/API bölgeleri:** {len(results)}

        **Endpoint adayları:** {len(candidates)}

        Bir sonraki aşamada gerçek maç istatistiklerini taşıyan
        endpoint'i doğrulayacağız.
        """
    )

    st.warning(
        "⚠️ Henüz bahis tahmini yapılmıyor. "
        "Önce StatsHub'dan gerçek veri kaynağını doğruluyoruz."
    )
