import streamlit as st
import requests
import json
import re
from html.parser import HTMLParser
from collections import Counter

st.set_page_config(
    page_title="StatsHub Quant Engine",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Quant Engine")
st.write("StatsHub sayfasındaki gerçek veri bloklarını otomatik keşfeder.")

# ============================================================
# HTML SCRIPT PARSER
# ============================================================

class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attrs_dict = dict(attrs)
            self.current = {
                "attrs": attrs_dict,
                "content": ""
            }

    def handle_data(self, data):
        if self.current is not None:
            self.current["content"] += data

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.current is not None:
            self.scripts.append(self.current)
            self.current = None


# ============================================================
# JSON PARSE
# ============================================================

def try_json(text):
    text = text.strip()

    if not text:
        return None

    try:
        return json.loads(text)
    except Exception:
        return None


# ============================================================
# RECURSIVE JSON WALKER
# ============================================================

def walk_json(obj, path="root"):
    results = []

    if isinstance(obj, dict):
        results.append((path, obj))

        for key, value in obj.items():
            results.extend(
                walk_json(value, f"{path}.{key}")
            )

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            results.extend(
                walk_json(value, f"{path}[{i}]")
            )

    return results


# ============================================================
# JSON OBJECT DISCOVERY
# ============================================================

def extract_json_candidates(text):
    candidates = []

    # Önce doğrudan JSON dene
    direct = try_json(text)

    if direct is not None:
        candidates.append(direct)

    # Script içerisinde gömülü JSON araması
    starts = []

    for i, char in enumerate(text):
        if char in "{[":
            starts.append(i)

    for start in starts:
        opening = text[start]

        if opening == "{":
            closing = "}"
        else:
            closing = "]"

        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):

            char = text[i]

            if escape:
                escape = False
                continue

            if char == "\\" and in_string:
                escape = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == opening:
                depth += 1

            elif char == closing:
                depth -= 1

                if depth == 0:
                    candidate = text[start:i + 1]

                    try:
                        parsed = json.loads(candidate)
                        candidates.append(parsed)
                    except Exception:
                        pass

                    break

    return candidates


# ============================================================
# DATA CLASSIFICATION
# ============================================================

def classify(obj, fixture_id="416477"):

    if not isinstance(obj, dict):
        return "OTHER", 0

    keys = {str(k).lower() for k in obj.keys()}
    values = {str(v).lower() for v in obj.values()}

    score = 0
    category = "OTHER"

    # Fixture
    if (
        str(obj.get("internalId")) == fixture_id
        or str(obj.get("internalId")) == "416477"
        or fixture_id in str(obj.get("slug", ""))
    ):
        return "FIXTURE", 100

    # Team
    team_keys = {
        "shortname",
        "countrySlug",
        "teamcolorsprimary",
        "foundationdate",
        "venueid"
    }

    team_score = len(keys.intersection(team_keys))

    if "name" in keys and team_score >= 2:
        category = "TEAM"
        score = max(score, 80)

    # Referee
    referee_keys = {
        "yellowcards",
        "redcards",
        "yellowredcards",
        "averagecards",
        "firstleaguedebutTimestamp".lower()
    }

    if len(keys.intersection(referee_keys)) >= 2:
        category = "REFEREE"
        score = max(score, 85)

    # Venue
    venue_keys = {
        "capacity",
        "cityname",
        "latitude",
        "longitude"
    }

    if len(keys.intersection(venue_keys)) >= 2:
        category = "VENUE"
        score = max(score, 75)

    # Tournament
    tournament_keys = {
        "categoryid",
        "primarycolorhex",
        "secondarycolorhex",
        "hasperformancegraph",
        "hasperformancegraph"
    }

    if (
        "name" in keys
        and len(keys.intersection(tournament_keys)) >= 2
    ):
        category = "TOURNAMENT"
        score = max(score, 70)

    # Player
    player_keys = {
        "playerid",
        "jerseynumber",
        "position",
        "preferredfoot",
        "height",
        "dateofbirth"
    }

    if len(keys.intersection(player_keys)) >= 1:
        category = "PLAYER"
        score = max(score, 80)

    # Stats
    stat_keys = {
        "shots",
        "shotsontarget",
        "goals",
        "assists",
        "xg",
        "possession",
        "corners",
        "passes",
        "keypasses",
        "rating",
        "tackles",
        "interceptions",
        "fouls",
        "offsides",
        "saves"
    }

    stat_score = len(keys.intersection(stat_keys))

    if stat_score >= 2:
        category = "STATISTICS"
        score = max(score, 90)

    # Lineup
    lineup_keys = {
        "lineup",
        "formation",
        "starting",
        "substitutes",
        "bench"
    }

    if len(keys.intersection(lineup_keys)) >= 2:
        category = "LINEUP"
        score = max(score, 85)

    return category, score


# ============================================================
# UI
# ============================================================

st.divider()

url = st.text_input(
    "StatsHub maç URL'sini gir:",
    value="https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🔍 GERÇEK VERİLERİ OTOMATİK BUL", type="primary"):

    if not url:
        st.warning("URL girmen gerekiyor.")
        st.stop()

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml"
        }

        with st.spinner("StatsHub sayfası analiz ediliyor..."):

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

        st.success(f"HTTP {response.status_code}")

        html = response.text

        st.write(
            f"📄 HTML boyutu: **{len(html):,} karakter**"
        )

        # ----------------------------------------------------
        # SCRIPTLERİ BUL
        # ----------------------------------------------------

        parser = ScriptParser()
        parser.feed(html)

        scripts = parser.scripts

        st.info(
            f"🔎 Sayfada **{len(scripts)} script bloğu** bulundu."
        )

        all_objects = []

        # ----------------------------------------------------
        # SCRIPT JSON TARAMA
        # ----------------------------------------------------

        for script_index, script in enumerate(scripts):

            content = script["content"]

            if not content.strip():
                continue

            candidates = extract_json_candidates(content)

            for candidate in candidates:

                for path, obj in walk_json(
                    candidate,
                    f"script[{script_index}]"
                ):

                    if isinstance(obj, dict):

                        category, score = classify(obj)

                        if score >= 50:

                            all_objects.append({
                                "script": script_index,
                                "path": path,
                                "category": category,
                                "score": score,
                                "data": obj
                            })

        # ----------------------------------------------------
        # DUPLICATE TEMİZLE
        # ----------------------------------------------------

        unique = {}

        for item in all_objects:

            try:
                fingerprint = json.dumps(
                    item["data"],
                    sort_keys=True,
                    ensure_ascii=False
                )
            except Exception:
                continue

            unique[fingerprint] = item

        all_objects = list(unique.values())

        all_objects.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # ----------------------------------------------------
        # SONUÇ
        # ----------------------------------------------------

        st.divider()

        st.subheader("📊 Otomatik Veri Keşfi")

        if not all_objects:

            st.error(
                "Gerçek futbol veri bloğu bulunamadı."
            )

        else:

            counter = Counter(
                x["category"]
                for x in all_objects
            )

            cols = st.columns(6)

            categories = [
                "FIXTURE",
                "TEAM",
                "PLAYER",
                "STATISTICS",
                "LINEUP",
                "REFEREE"
            ]

            for col, cat in zip(cols, categories):

                col.metric(
                    cat,
                    counter.get(cat, 0)
                )

            st.divider()

            st.subheader("🎯 Bulunan Gerçek Veri Blokları")

            for i, item in enumerate(all_objects[:30], 1):

                category = item["category"]
                score = item["score"]

                with st.expander(
                    f"{i}. {category} | Güven skoru: {score} | Script #{item['script']}"
                ):

                    st.write(
                        f"JSON yolu: `{item['path']}`"
                    )

                    st.json(item["data"])

        st.divider()

        st.caption(
            "Bu aşamada veri değiştirilmez veya tahmin üretilmez. "
            "Amaç StatsHub sayfasındaki gerçek veri yapısını keşfetmektir."
        )

    except Exception as e:

        st.error("Bir hata oluştu.")

        st.exception(e)
