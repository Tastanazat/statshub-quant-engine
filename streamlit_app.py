import streamlit as st
import requests
import json
import re
from html.parser import HTMLParser
from collections import Counter


# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="StatsHub Quant Engine",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Quant Engine")
st.write(
    "StatsHub sayfasındaki gerçek futbol verilerini otomatik keşfetme sistemi."
)


# ============================================================
# SCRIPT PARSER
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
# JSON DENEME
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
# JSON İÇERİSİNDEKİ TÜM DICT'LERİ BUL
# ============================================================

def walk_json(obj, path="root"):

    results = []

    if isinstance(obj, dict):

        results.append((path, obj))

        for key, value in obj.items():

            results.extend(
                walk_json(
                    value,
                    f"{path}.{key}"
                )
            )

    elif isinstance(obj, list):

        for index, value in enumerate(obj):

            results.extend(
                walk_json(
                    value,
                    f"{path}[{index}]"
                )
            )

    return results


# ============================================================
# GÖMÜLÜ JSON BULUCU
# ============================================================

def extract_json_candidates(text):

    candidates = []

    # 1 — Metnin tamamı JSON mu?
    direct = try_json(text)

    if direct is not None:

        candidates.append(direct)

    # 2 — JSON object / array ara
    for start in range(len(text)):

        if text[start] not in "{[":
            continue

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
# VERİ SINIFLANDIRMA
# ============================================================

def classify(obj, fixture_id="416477"):

    if not isinstance(obj, dict):

        return "OTHER", 0

    # --------------------------------------------------------
    # SEO / BREADCRUMB ELEME
    # --------------------------------------------------------

    if obj.get("@type") in [
        "ListItem",
        "BreadcrumbList"
    ]:

        return "SEO", 0

    keys = {
        str(k).lower()
        for k in obj.keys()
    }

    # --------------------------------------------------------
    # FIXTURE
    # --------------------------------------------------------

    if (
        str(obj.get("internalId")) == fixture_id
        or str(obj.get("id")) == "16938896"
        or fixture_id in str(obj.get("slug", ""))
    ):

        return "FIXTURE", 100

    # --------------------------------------------------------
    # REFEREE
    # --------------------------------------------------------

    referee_keys = {
        "yellowcards",
        "redcards",
        "yellowredcards",
        "averagecards",
        "firstleaguedebutTimestamp".lower(),
        "games"
    }

    if len(
        keys.intersection(referee_keys)
    ) >= 3:

        return "REFEREE", 95

    # --------------------------------------------------------
    # VENUE
    # --------------------------------------------------------

    venue_keys = {
        "capacity",
        "cityname",
        "latitude",
        "longitude"
    }

    if len(
        keys.intersection(venue_keys)
    ) >= 2:

        return "VENUE", 90

    # --------------------------------------------------------
    # TOURNAMENT
    # --------------------------------------------------------

    tournament_keys = {
        "categoryid",
        "primarycolorhex",
        "secondarycolorhex",
        "hasperformancegraph",
        "haseventplayerstatistics",
        "displayinversehomeaway",
        "onfortelegrambot"
    }

    if (
        "name" in keys
        and len(
            keys.intersection(tournament_keys)
        ) >= 2
    ):

        return "TOURNAMENT", 90

    # --------------------------------------------------------
    # GERÇEK PLAYER KONTROLÜ
    # --------------------------------------------------------

    player_keys = {
        "playerid",
        "jerseynumber",
        "preferredfoot",
        "dateofbirth",
        "nationality",
        "height",
        "position",
        "shirt_number"
    }

    player_score = len(
        keys.intersection(player_keys)
    )

    # ÖNEMLİ:
    # Sadece "position" olması PLAYER değildir.
    if player_score >= 2:

        return "PLAYER", 90

    # --------------------------------------------------------
    # İSTATİSTİK
    # --------------------------------------------------------

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
        "saves",
        "bigchances",
        "accuratepasses",
        "totalshots",
        "shotsinsidebox",
        "shotsoutsidebox"
    }

    stat_score = len(
        keys.intersection(stat_keys)
    )

    if stat_score >= 2:

        return "STATISTICS", 95

    # --------------------------------------------------------
    # LINEUP
    # --------------------------------------------------------

    lineup_keys = {
        "lineup",
        "formation",
        "starting",
        "substitutes",
        "bench",
        "players"
    }

    lineup_score = len(
        keys.intersection(lineup_keys)
    )

    if lineup_score >= 2:

        return "LINEUP", 90

    # --------------------------------------------------------
    # TEAM
    # --------------------------------------------------------

    team_keys = {
        "shortname",
        "countryslug",
        "teamcolorsprimary",
        "foundationdate"
    }

    team_score = len(
        keys.intersection(team_keys)
    )

    if (
        "name" in keys
        and team_score >= 2
    ):

        return "TEAM", 90

    return "OTHER", 0


# ============================================================
# URL
# ============================================================

st.divider()

url = st.text_input(
    "StatsHub maç URL'sini gir:",
    value=(
        "https://www.statshub.com/fixture/"
        "psv-eindhoven-vs-shakhtar-donetsk-mtv02l/"
        "416477"
    )
)


# ============================================================
# ANA BUTON
# ============================================================

if st.button(
    "🔍 STATSHUB VERİLERİNİ TARA",
    type="primary"
):

    if not url:

        st.warning(
            "Lütfen StatsHub maç URL'si gir."
        )

        st.stop()

    try:

        headers = {

            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            ),

            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),

            "Accept-Language":
                "tr-TR,tr;q=0.9,en;q=0.8"
        }

        with st.spinner(
            "StatsHub sayfası taranıyor..."
        ):

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

        # ----------------------------------------------------
        # HTTP
        # ----------------------------------------------------

        st.success(
            f"HTTP Status: {response.status_code}"
        )

        html = response.text

        st.info(
            f"📄 HTML boyutu: "
            f"{len(html):,} karakter"
        )

        # ----------------------------------------------------
        # SCRIPT SAYISI
        # ----------------------------------------------------

        parser = ScriptParser()

        parser.feed(html)

        scripts = parser.scripts

        st.info(
            f"🔎 {len(scripts)} script bloğu bulundu."
        )

        # ----------------------------------------------------
        # NEXT DATA KONTROLÜ
        # ----------------------------------------------------

        next_data_found = False

        next_match = re.search(
            r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>'
            r'(.*?)'
            r'</script>',
            html,
            re.S | re.I
        )

        if next_match:

            next_data_found = True

            try:

                next_data = json.loads(
                    next_match.group(1)
                )

                st.success(
                    "✅ __NEXT_DATA__ bulundu."
                )

            except Exception:

                next_data = None

                st.warning(
                    "⚠️ __NEXT_DATA__ bulundu fakat JSON okunamadı."
                )

        else:

            next_data = None

            st.warning(
                "ℹ️ __NEXT_DATA__ bulunamadı."
            )

        # ----------------------------------------------------
        # TÜM JSONLARI TOPLA
        # ----------------------------------------------------

        all_objects = []

        for script_index, script in enumerate(
            scripts
        ):

            content = script["content"]

            if not content.strip():
                continue

            candidates = extract_json_candidates(
                content
            )

            for candidate in candidates:

                nodes = walk_json(
                    candidate,
                    f"script[{script_index}]"
                )

                for path, obj in nodes:

                    category, score = classify(
                        obj
                    )

                    if score >= 50:

                        all_objects.append({

                            "script":
                                script_index,

                            "path":
                                path,

                            "category":
                                category,

                            "score":
                                score,

                            "data":
                                obj
                        })

        # ----------------------------------------------------
        # NEXT DATA'YI DA TARA
        # ----------------------------------------------------

        if next_data is not None:

            for path, obj in walk_json(
                next_data,
                "NEXT_DATA"
            ):

                category, score = classify(
                    obj
                )

                if score >= 50:

                    all_objects.append({

                        "script":
                            "__NEXT_DATA__",

                        "path":
                            path,

                        "category":
                            category,

                        "score":
                            score,

                        "data":
                            obj
                    })

        # ----------------------------------------------------
        # DUPLICATE TEMİZLEME
        # ----------------------------------------------------

        unique = {}

        for item in all_objects:

            try:

                fingerprint = json.dumps(
                    item["data"],
                    sort_keys=True,
                    ensure_ascii=False
                )

                unique[fingerprint] = item

            except Exception:

                pass

        all_objects = list(
            unique.values()
        )

        # ----------------------------------------------------
        # PUANA GÖRE SIRALA
        # ----------------------------------------------------

        all_objects.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        # ----------------------------------------------------
        # SONUÇLAR
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "📊 Otomatik Veri Keşfi"
        )

        counter = Counter(
            item["category"]
            for item in all_objects
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

        for col, category in zip(
            cols,
            categories
        ):

            col.metric(
                category,
                counter.get(
                    category,
                    0
                )
            )

        # ----------------------------------------------------
        # ÖNEMLİ VERİLER
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🎯 Bulunan Gerçek Veri Blokları"
        )

        if not all_objects:

            st.error(
                "Gerçek veri bloğu bulunamadı."
            )

        else:

            for i, item in enumerate(
                all_objects[:40],
                1
            ):

                category = item[
                    "category"
                ]

                score = item[
                    "score"
                ]

                with st.expander(
                    f"{i}. {category} | "
                    f"Güven: {score} | "
                    f"Script: {item['script']}"
                ):

                    st.write(
                        "JSON yolu:"
                    )

                    st.code(
                        item["path"]
                    )

                    st.json(
                        item["data"]
                    )

        # ----------------------------------------------------
        # İSTATİSTİK ÖZETİ
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "📋 Veri Durumu"
        )

        if counter.get(
            "STATISTICS",
            0
        ) > 0:

            st.success(
                "🎯 Gerçek istatistik blokları bulundu!"
            )

        else:

            st.warning(
                "Henüz takım/oyuncu istatistik "
                "bloğu bulunamadı. Bir sonraki "
                "aşamada sayfanın veri endpointlerini "
                "araştıracağız."
            )

        # ----------------------------------------------------
        # SON NOT
        # ----------------------------------------------------

        st.divider()

        st.caption(
            "Bu aşamada hiçbir veri değiştirilmez "
            "ve bahis tahmini üretilmez. "
            "Amaç StatsHub veri yapısını keşfetmektir."
        )

    except Exception as e:

        st.error(
            "❌ Bir hata oluştu."
        )

        st.exception(e)
