import streamlit as st
import requests
import re
import json

st.set_page_config(
    page_title="StatsHub Veri Analizi",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Veri Yapısı Analizi")

url = st.text_input(
    "StatsHub maç URL'si",
    "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🔎 VERİ YAPISINI BUL", type="primary"):

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml"
    }

    with st.spinner("StatsHub verisi inceleniyor..."):

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            html = response.text

        except Exception as e:
            st.error(f"Hata: {e}")
            st.stop()

    st.success(f"HTTP {response.status_code}")

    st.write(
        f"HTML uzunluğu: **{len(html):,} karakter**"
    )

    # =====================================================
    # 1. BİLDİĞİMİZ MAÇ KİMLİKLERİ
    # =====================================================

    st.subheader("🆔 1. Maç kimlikleri")

    fixture_match = re.search(
        r'"internalId"\s*:\s*(\d+)',
        html
    )

    home_match = re.search(
        r'"homeTeamId"\s*:\s*(\d+)',
        html
    )

    away_match = re.search(
        r'"awayTeamId"\s*:\s*(\d+)',
        html
    )

    if fixture_match:
        st.write(
            f"**Fixture ID:** `{fixture_match.group(1)}`"
        )

    if home_match:
        st.write(
            f"**Home Team ID:** `{home_match.group(1)}`"
        )

    if away_match:
        st.write(
            f"**Away Team ID:** `{away_match.group(1)}`"
        )

    # =====================================================
    # 2. SAYFADAKİ JSON BLOKLARINI BUL
    # =====================================================

    st.subheader("📦 2. JSON veri blokları")

    json_blocks = []

    # Script içindeki JSON benzeri alanları bul
    script_pattern = r"<script[^>]*>(.*?)</script>"

    scripts = re.findall(
        script_pattern,
        html,
        flags=re.I | re.S
    )

    for script in scripts:

        text = script.strip()

        if len(text) < 20:
            continue

        # Doğrudan JSON
        try:

            data = json.loads(text)

            json_blocks.append(data)

        except Exception:
            pass

        # __next_f / RSC gibi yapılarda JSON parçaları
        if "__next_f" in text:

            pieces = re.findall(
                r'\{.*?\}',
                text,
                flags=re.S
            )

            for piece in pieces[:100]:

                try:

                    data = json.loads(piece)

                    json_blocks.append(data)

                except Exception:
                    pass

    st.write(
        f"Bulunan gerçek JSON nesnesi: **{len(json_blocks)}**"
    )

    # =====================================================
    # 3. JSON İÇERİĞİNİ SINIFLANDIR
    # =====================================================

    fixture_data = []
    team_data = []
    player_data = []
    stats_data = []
    lineup_data = []
    other_data = []

    def classify(obj):

        if not isinstance(obj, dict):
            return "other"

        keys = {
            str(k).lower()
            for k in obj.keys()
        }

        # Fixture
        if (
            "hometeamid" in keys
            and "awayteamid" in keys
        ):
            return "fixture"

        # Lineup
        if (
            "lineup" in keys
            or "formation" in keys
        ):
            return "lineup"

        # Statistics
        stat_words = {
            "shots",
            "shotsontarget",
            "possession",
            "corners",
            "goals",
            "xg",
            "expectedgoals",
            "passes"
        }

        if len(keys.intersection(stat_words)) >= 2:
            return "statistics"

        # Player
        player_words = {
            "player",
            "playerid",
            "firstname",
            "lastname",
            "position"
        }

        if len(keys.intersection(player_words)) >= 2:
            return "player"

        # Team
        if (
            "teamid" in keys
            and (
                "name" in keys
                or "shortname" in keys
            )
        ):
            return "team"

        return "other"

    for obj in json_blocks:

        category = classify(obj)

        if category == "fixture":
            fixture_data.append(obj)

        elif category == "team":
            team_data.append(obj)

        elif category == "player":
            player_data.append(obj)

        elif category == "statistics":
            stats_data.append(obj)

        elif category == "lineup":
            lineup_data.append(obj)

        else:
            other_data.append(obj)

    # =====================================================
    # 4. SONUÇLAR
    # =====================================================

    st.subheader("📊 3. Veri sınıflandırması")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Fixture",
        len(fixture_data)
    )

    col2.metric(
        "Team",
        len(team_data)
    )

    col3.metric(
        "Player",
        len(player_data)
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Statistics",
        len(stats_data)
    )

    col5.metric(
        "Lineup",
        len(lineup_data)
    )

    col6.metric(
        "Other",
        len(other_data)
    )

    # =====================================================
    # 5. BULUNAN VERİLERİ GÖSTER
    # =====================================================

    categories = [
        ("Fixture", fixture_data),
        ("Team", team_data),
        ("Player", player_data),
        ("Statistics", stats_data),
        ("Lineup", lineup_data)
    ]

    for name, data in categories:

        if not data:
            continue

        st.subheader(
            f"🔍 {name} verileri"
        )

        for i, item in enumerate(
            data[:10],
            1
        ):

            with st.expander(
                f"{name} #{i}"
            ):

                st.json(item)

    # =====================================================
    # 6. ÖNEMLİ KELİMELER
    # =====================================================

    st.subheader("🔎 4. StatsHub veri alanları")

    keywords = [
        "shots",
        "shotsOnTarget",
        "xg",
        "expectedGoals",
        "possession",
        "corners",
        "goals",
        "passes",
        "lineup",
        "playerStats",
        "teamStats",
        "statistics"
    ]

    for word in keywords:

        count = len(
            re.findall(
                re.escape(word),
                html,
                flags=re.I
            )
        )

        if count > 0:

            st.write(
                f"**{word}:** {count}"
            )

    st.divider()

    st.success(
        "Tarama tamamlandı."
    )

    st.info(
        "Şimdi sonuç ekranında hangi gerçek veri nesnelerinin "
        "StatsHub HTML'sinde bulunduğunu göreceğiz."
    )
