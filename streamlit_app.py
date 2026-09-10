import streamlit as st
import requests
import re

st.set_page_config(
    page_title="StatsHub Data Discovery",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Data Discovery")

url = st.text_input(
    "StatsHub maç URL'si:",
    value="https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🔎 VERİ YAPISINI ANALİZ ET", type="primary"):

    if not url:
        st.error("URL gir.")
        st.stop()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 16; Mobile) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0 Mobile Safari/537.36"
        )
    }

    try:

        with st.spinner("StatsHub verisi inceleniyor..."):

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

        html = response.text

        st.success("✅ StatsHub sayfası alındı.")

        # ------------------------------------------------
        # 1. TEMEL BİLGİLER
        # ------------------------------------------------

        st.subheader("📊 Temel Bilgiler")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("HTTP", response.status_code)

        with col2:
            st.metric("HTML", f"{len(html):,} karakter")

        with col3:
            st.metric(
                "Script Sayısı",
                len(re.findall(r"<script", html, re.I))
            )

        # ------------------------------------------------
        # 2. ÖNEMLİ VERİ YAPILARI
        # ------------------------------------------------

        st.subheader("🧬 Veri Yapısı Kontrolü")

        checks = {
            "__NEXT_DATA__": "__NEXT_DATA__",
            "JSON-LD": 'application/ld+json',
            "API ifadeleri": "/api/",
            "GraphQL": "graphql",
            "Player": "player",
            "Team": "team",
            "Lineup": "lineup",
            "Stats": "stats",
            "Fixture ID": "416477"
        }

        for name, search_text in checks.items():

            if search_text.lower() in html.lower():
                st.success(f"✅ {name} bulundu")
            else:
                st.warning(f"⚠️ {name} bulunamadı")

        # ------------------------------------------------
        # 3. SCRIPT BLOKLARI
        # ------------------------------------------------

        st.subheader("📦 Script Veri Blokları")

        scripts = re.findall(
            r"<script[^>]*>(.*?)</script>",
            html,
            re.I | re.S
        )

        st.write(
            f"Toplam script bloğu: **{len(scripts)}**"
        )

        for i, script in enumerate(scripts):

            script_clean = script.strip()

            if len(script_clean) > 100:

                with st.expander(
                    f"Script #{i+1} — {len(script_clean):,} karakter"
                ):

                    st.code(
                        script_clean[:5000],
                        language="javascript"
                    )

        # ------------------------------------------------
        # 4. API URL'LERİ
        # ------------------------------------------------

        st.subheader("🌐 Bulunan API / Veri URL'leri")

        api_urls = sorted(
            set(
                re.findall(
                    r'https?://[^"\']+',
                    html
                )
            )
        )

        if api_urls:

            for api in api_urls[:100]:
                st.code(api)

        else:

            st.info(
                "HTML içinde açık HTTP URL bulunamadı."
            )

        # ------------------------------------------------
        # 5. JSON BENZERİ BLOKLAR
        # ------------------------------------------------

        st.subheader("🧩 JSON Benzeri Veri")

        json_patterns = [
            r'\{[^{}]{50,}\}',
            r'\[[^\[\]]{50,}\]'
        ]

        found = []

        for pattern in json_patterns:

            matches = re.findall(
                pattern,
                html,
                re.S
            )

            found.extend(matches)

        found = sorted(
            set(found),
            key=len,
            reverse=True
        )

        st.write(
            f"Bulunan aday veri blokları: **{len(found)}**"
        )

        for i, block in enumerate(found[:20]):

            with st.expander(
                f"Aday veri #{i+1} — {len(block):,} karakter"
            ):

                st.code(
                    block[:5000]
                )

        # ------------------------------------------------
        # 6. PLAYER / TEAM ÇEVRESİ
        # ------------------------------------------------

        st.subheader("👤 Player / Team Veri Bölgeleri")

        keywords = [
            "player",
            "team",
            "lineup",
            "shots",
            "goals",
            "assists",
            "passes",
            "corners",
            "xg",
            "possession"
        ]

        for keyword in keywords:

            positions = [
                m.start()
                for m in re.finditer(
                    keyword,
                    html,
                    re.I
                )
            ]

            if positions:

                st.write(
                    f"**{keyword}** → "
                    f"{len(positions)} kez bulundu"
                )

                first_pos = positions[0]

                with st.expander(
                    f"{keyword} ilk veri bölgesi"
                ):

                    start = max(
                        0,
                        first_pos - 1000
                    )

                    end = min(
                        len(html),
                        first_pos + 3000
                    )

                    st.code(
                        html[start:end]
                    )

    except Exception as e:

        st.error(
            f"❌ Hata: {e}"
        )
