import streamlit as st
import requests
import re
from urllib.parse import urljoin

st.set_page_config(
    page_title="StatsHub Network Finder",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 StatsHub Network Finder")

url = st.text_input(
    "StatsHub maç URL'si",
    "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🚀 NETWORK ÇAĞRILARINI BUL", type="primary"):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9"
    }

    # --------------------------------------------------
    # SAYFAYI AL
    # --------------------------------------------------

    with st.spinner("StatsHub sayfası alınıyor..."):

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            html = response.text

        except Exception as e:
            st.error(f"Bağlantı hatası: {e}")
            st.stop()

    st.success(
        f"StatsHub bağlantısı başarılı — HTTP {response.status_code}"
    )

    st.write(
        f"HTML uzunluğu: **{len(html):,} karakter**"
    )

    # --------------------------------------------------
    # JAVASCRIPT DOSYALARINI BUL
    # --------------------------------------------------

    st.subheader("📦 JavaScript dosyaları")

    scripts = re.findall(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        html,
        flags=re.I
    )

    js_urls = []

    for src in scripts:

        full_url = urljoin(url, src)

        if full_url not in js_urls:
            js_urls.append(full_url)

    st.write(
        f"Bulunan JavaScript: **{len(js_urls)}**"
    )

    # --------------------------------------------------
    # JS DOSYALARINI İNDİR
    # --------------------------------------------------

    js_files = []

    progress = st.progress(0)

    for i, js_url in enumerate(js_urls):

        try:

            r = requests.get(
                js_url,
                headers=headers,
                timeout=10
            )

            if r.status_code == 200:

                text = r.text

                # Güvenlik: devasa dosyaları sınırlıyoruz
                if len(text) > 3_000_000:
                    text = text[:3_000_000]

                js_files.append({
                    "url": js_url,
                    "text": text
                })

        except Exception:
            pass

        progress.progress(
            (i + 1) / max(len(js_urls), 1)
        )

    st.success(
        f"{len(js_files)} JavaScript dosyası indirildi."
    )

    # --------------------------------------------------
    # SADECE API ÇAĞRISI ÇEVRESİNDEKİ KODU BUL
    # --------------------------------------------------

    st.subheader("🔎 Network çağrıları")

    search_patterns = [
        ("FETCH", r'\bfetch\s*\('),
        ("AXIOS", r'\baxios\b'),
        ("XMLHttpRequest", r'\bXMLHttpRequest\b'),
        ("GRAPHQL", r'\bgraphql\b'),
        ("API PATH", r'["\'][^"\']*/api/[^"\']*["\']'),
        ("BASE URL", r'\bbaseURL\b'),
        ("API URL", r'\bapiUrl\b'),
        ("EVENT ID", r'\beventId\b'),
        ("MATCH STATS", r'\bmatchStats\b'),
        ("PLAYER STATS", r'\bplayerStats\b'),
        ("TEAM STATS", r'\bteamStats\b'),
        ("LINEUPS", r'\blineups\b')
    ]

    findings = []

    for js in js_files:

        text = js["text"]

        for name, pattern in search_patterns:

            matches = list(
                re.finditer(
                    pattern,
                    text,
                    flags=re.I
                )
            )

            # Her dosyadan en fazla 5 bölge
            for match in matches[:5]:

                start = max(
                    0,
                    match.start() - 500
                )

                end = min(
                    len(text),
                    match.end() + 1200
                )

                snippet = text[start:end]

                findings.append({
                    "name": name,
                    "url": js["url"],
                    "snippet": snippet
                })

    st.write(
        f"Bulunan önemli kod bölgesi: **{len(findings)}**"
    )

    # --------------------------------------------------
    # SADECE İSTATİSTİKLE İLGİLİ OLANLARI GÖSTER
    # --------------------------------------------------

    important_words = [
        "fetch",
        "axios",
        "/api/",
        "graphql",
        "eventId",
        "matchStats",
        "playerStats",
        "teamStats",
        "lineups"
    ]

    filtered = []

    for item in findings:

        combined = (
            item["name"] +
            " " +
            item["snippet"]
        ).lower()

        score = 0

        for word in important_words:

            if word.lower() in combined:
                score += 1

        item["score"] = score

        if score >= 1:
            filtered.append(item)

    filtered.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------------------------
    # SONUÇLARI GÖSTER
    # --------------------------------------------------

    st.subheader("🎯 En önemli sonuçlar")

    if not filtered:

        st.warning(
            "Statik JavaScript taramasında network çağrısı bulunamadı."
        )

    else:

        for i, item in enumerate(
            filtered[:30],
            1
        ):

            with st.expander(
                f"#{i} — {item['name']} — Skor {item['score']}"
            ):

                st.write("JavaScript dosyası:")

                st.code(
                    item["url"],
                    language="text"
                )

                st.write("Kod:")

                st.code(
                    item["snippet"],
                    language="javascript"
                )

    # --------------------------------------------------
    # MAÇ ID'LERİ
    # --------------------------------------------------

    st.subheader("🆔 Maç kimlikleri")

    patterns = {
        "Fixture": r'"internalId"\s*:\s*(\d+)',
        "PSV / Home": r'"homeTeamId"\s*:\s*(\d+)',
        "Shakhtar / Away": r'"awayTeamId"\s*:\s*(\d+)'
    }

    for name, pattern in patterns.items():

        match = re.search(
            pattern,
            html,
            flags=re.I
        )

        if match:

            st.write(
                f"**{name}:** `{match.group(1)}`"
            )

    st.divider()

    st.info(
        "Buradaki amaç henüz istatistikleri çekmek değil. "
        "Önce StatsHub'ın kullandığı gerçek network/API çağrısını "
        "tespit ediyoruz."
    )
