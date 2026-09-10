import streamlit as st
import requests
import re

st.set_page_config(
    page_title="StatsHub Core API Finder",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 StatsHub Core API Finder")

JS_URL = (
    "https://www.statshub.com/_next/static/chunks/pages/"
    "fixture/%5BfixtureSlug%5D/%5BfixtureId%5D-1a82e0e92c7c1aa6.js"
)

if st.button("🔍 ANA VERİ KAYNAĞINI BUL", type="primary"):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
    }

    with st.spinner("StatsHub fixture JavaScript okunuyor..."):

        try:
            response = requests.get(
                JS_URL,
                headers=headers,
                timeout=20
            )

            js = response.text

        except Exception as e:
            st.error(f"Hata: {e}")
            st.stop()

    st.success(
        f"JavaScript alındı — HTTP {response.status_code}"
    )

    st.write(
        f"Dosya boyutu: **{len(js):,} karakter**"
    )

    # =====================================================
    # 1 — EVENT ID
    # =====================================================

    st.subheader("🆔 1. EVENT ID kaynakları")

    patterns_event = [
        r'aZ\.events\.id',
        r'events\.id',
        r'eventId',
        r'eventID'
    ]

    event_positions = []

    for pattern in patterns_event:

        for match in re.finditer(
            pattern,
            js,
            flags=re.I
        ):

            event_positions.append(match.start())

    event_positions = sorted(
        set(event_positions)
    )

    st.write(
        f"Event ID ile ilgili bölge: **{len(event_positions)}**"
    )

    for i, pos in enumerate(
        event_positions[:15],
        1
    ):

        start = max(0, pos - 1000)
        end = min(len(js), pos + 1500)

        with st.expander(
            f"EVENT ID #{i}"
        ):

            st.code(
                js[start:end],
                language="javascript"
            )

    # =====================================================
    # 2 — t2 HOME PLAYER STATS
    # =====================================================

    st.subheader("🏠 2. t2 — Home Player Stats")

    t2_positions = [
        m.start()
        for m in re.finditer(
            r'\bt2\b',
            js
        )
    ]

    st.write(
        f"t2 kullanım sayısı: **{len(t2_positions)}**"
    )

    for i, pos in enumerate(
        t2_positions[:15],
        1
    ):

        start = max(0, pos - 1000)
        end = min(len(js), pos + 1500)

        with st.expander(
            f"t2 #{i}"
        ):

            st.code(
                js[start:end],
                language="javascript"
            )

    # =====================================================
    # 3 — t9 AWAY PLAYER STATS
    # =====================================================

    st.subheader("✈️ 3. t9 — Away Player Stats")

    t9_positions = [
        m.start()
        for m in re.finditer(
            r'\bt9\b',
            js
        )
    ]

    st.write(
        f"t9 kullanım sayısı: **{len(t9_positions)}**"
    )

    for i, pos in enumerate(
        t9_positions[:15],
        1
    ):

        start = max(0, pos - 1000)
        end = min(len(js), pos + 1500)

        with st.expander(
            f"t9 #{i}"
        ):

            st.code(
                js[start:end],
                language="javascript"
            )

    # =====================================================
    # 4 — FIXTURE ID
    # =====================================================

    st.subheader("📌 4. Fixture ID / aD")

    ad_positions = [
        m.start()
        for m in re.finditer(
            r'\baD\b',
            js
        )
    ]

    st.write(
        f"aD kullanım sayısı: **{len(ad_positions)}**"
    )

    for i, pos in enumerate(
        ad_positions[:10],
        1
    ):

        start = max(0, pos - 700)
        end = min(len(js), pos + 1200)

        with st.expander(
            f"aD #{i}"
        ):

            st.code(
                js[start:end],
                language="javascript"
            )

    # =====================================================
    # 5 — FETCH
    # =====================================================

    st.subheader("🌐 5. FETCH çağrıları")

    fetch_positions = [
        m.start()
        for m in re.finditer(
            r'\bfetch\s*\(',
            js,
            flags=re.I
        )
    ]

    st.write(
        f"Fetch sayısı: **{len(fetch_positions)}**"
    )

    for i, pos in enumerate(
        fetch_positions[:30],
        1
    ):

        start = max(0, pos - 800)
        end = min(len(js), pos + 1800)

        snippet = js[start:end]

        # İlgisiz çağrıları mümkün olduğunca ayır
        keywords = [
            "/api/",
            "event",
            "fixture",
            "player",
            "team",
            "stat",
            "lineup",
            "match"
        ]

        score = sum(
            1
            for word in keywords
            if word.lower() in snippet.lower()
        )

        with st.expander(
            f"FETCH #{i} — İlgililik skoru: {score}"
        ):

            st.code(
                snippet,
                language="javascript"
            )

    # =====================================================
    # 6 — API PATH'LERİ
    # =====================================================

    st.subheader("🔗 6. API yolları")

    api_matches = re.findall(
        r'["\']([^"\']*/api/[^"\']*)["\']',
        js,
        flags=re.I
    )

    api_unique = []

    for value in api_matches:

        if value not in api_unique:
            api_unique.append(value)

    st.write(
        f"Bulunan API yolu: **{len(api_unique)}**"
    )

    for i, value in enumerate(
        api_unique[:50],
        1
    ):

        st.code(
            f"{i}. {value}",
            language="text"
        )

    # =====================================================
    # 7 — PLAYER / TEAM STATS KULLANIMI
    # =====================================================

    st.subheader("📊 7. Player / Team Stats")

    important_patterns = [
        "homeTeamPlayerStats",
        "awayTeamPlayerStats",
        "playerStats",
        "teamStats",
        "matchStats",
        "statistics",
        "lineups"
    ]

    for word in important_patterns:

        positions = [
            m.start()
            for m in re.finditer(
                re.escape(word),
                js,
                flags=re.I
            )
        ]

        st.write(
            f"**{word}:** {len(positions)}"
        )

    # =====================================================
    # SONUÇ
    # =====================================================

    st.divider()

    st.success(
        "Ana fixture JavaScript dosyasının taraması tamamlandı."
    )

    st.info(
        "Özellikle EVENT ID, t2, t9 ve FETCH bölümlerini "
        "inceleyeceğiz. Gerçek StatsHub istatistik API'sini "
        "buradan ayıklamaya çalışacağız."
    )
