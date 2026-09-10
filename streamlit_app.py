import streamlit as st
import requests
import re
from urllib.parse import urljoin
from collections import defaultdict


# ============================================================
# SAYFA
# ============================================================

st.set_page_config(
    page_title="StatsHub API Finder",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 StatsHub Gerçek API Finder")

st.write(
    "StatsHub JavaScript dosyalarını tarar, "
    "gerçek futbol veri endpointi olabilecek adresleri "
    "puanlayarak öne çıkarır."
)

st.info(
    "⚠️ Bu aşamada bahis tahmini yapılmaz. "
    "Sadece StatsHub veri kaynağı bulunur."
)


# ============================================================
# URL
# ============================================================

url = st.text_input(
    "StatsHub maç URL'si:",
    value=(
        "https://www.statshub.com/fixture/"
        "psv-eindhoven-vs-shakhtar-donetsk-mtv02l/"
        "416477"
    )
)


# ============================================================
# HTTP
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
}


# ============================================================
# SCRIPT URL BUL
# ============================================================

def find_script_urls(html, page_url):

    pattern = re.compile(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        re.I
    )

    results = set()

    for src in pattern.findall(html):

        full_url = urljoin(
            page_url,
            src
        )

        results.add(full_url)

    return sorted(results)


# ============================================================
# GEREKSİZ URL KONTROLÜ
# ============================================================

def is_noise(value):

    low = value.lower()

    noise_words = [
        "fontshare",
        "fonts.googleapis",
        "googleapis",
        "woff",
        "woff2",
        "sentry",
        "umami",
        "analytics",
        "facebook",
        "twitter",
        "instagram",
        "youtube",
        "schema.org",
        "cloudflare"
    ]

    for word in noise_words:

        if word in low:
            return True

    return False


# ============================================================
# ENDPOINT PUANLAMA
# ============================================================

def score_endpoint(value):

    low = value.lower()

    if is_noise(value):

        return -100, ["NOISE"]


    score = 0
    reasons = []


    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    if "/api/" in low:

        score += 30
        reasons.append("/api/")


    if "graphql" in low:

        score += 30
        reasons.append("graphql")


    # --------------------------------------------------------
    # FIXTURE
    # --------------------------------------------------------

    if "fixture" in low:

        score += 25
        reasons.append("fixture")


    if "416477" in low:

        score += 40
        reasons.append("MATCH_ID")


    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    if "statistics" in low:

        score += 50
        reasons.append("statistics")


    if "statistic" in low:

        score += 40
        reasons.append("statistic")


    # --------------------------------------------------------
    # PLAYER
    # --------------------------------------------------------

    if "player" in low:

        score += 25
        reasons.append("player")


    # --------------------------------------------------------
    # TEAM
    # --------------------------------------------------------

    if "team" in low:

        score += 20
        reasons.append("team")


    # --------------------------------------------------------
    # LINEUP
    # --------------------------------------------------------

    if "lineup" in low:

        score += 40
        reasons.append("lineup")


    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    if "events" in low:

        score += 35
        reasons.append("events")


    if "/event" in low:

        score += 30
        reasons.append("event")


    # --------------------------------------------------------
    # SHOTS
    # --------------------------------------------------------

    if "shots" in low:

        score += 35
        reasons.append("shots")


    # --------------------------------------------------------
    # XG
    # --------------------------------------------------------

    if "xg" in low:

        score += 45
        reasons.append("xg")


    if "expected-goal" in low:

        score += 45
        reasons.append("expected-goals")


    # --------------------------------------------------------
    # POSSESSION
    # --------------------------------------------------------

    if "possession" in low:

        score += 30
        reasons.append("possession")


    # --------------------------------------------------------
    # CORNERS
    # --------------------------------------------------------

    if "corner" in low:

        score += 25
        reasons.append("corner")


    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    if "momentum" in low:

        score += 30
        reasons.append("momentum")


    # --------------------------------------------------------
    # MATCH
    # --------------------------------------------------------

    if "match" in low:

        score += 20
        reasons.append("match")


    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    if ".json" in low:

        score += 20
        reasons.append("json")


    return score, reasons


# ============================================================
# JS İÇERİĞİNDEN ADRESLERİ BUL
# ============================================================

def extract_strings(js):

    results = set()


    patterns = [

        # URL
        r'https?://[^"\'\s<>]+',

        # /api/...
        r'["\'](/api/[^"\']+)["\']',

        # fixture
        r'["\']([^"\']*fixture[^"\']*)["\']',

        # statistics
        r'["\']([^"\']*statistics[^"\']*)["\']',

        # statistic
        r'["\']([^"\']*statistic[^"\']*)["\']',

        # lineup
        r'["\']([^"\']*lineup[^"\']*)["\']',

        # player
        r'["\']([^"\']*player[^"\']*)["\']',

        # team
        r'["\']([^"\']*team[^"\']*)["\']',

        # events
        r'["\']([^"\']*events[^"\']*)["\']',

        # shots
        r'["\']([^"\']*shots[^"\']*)["\']',

        # xg
        r'["\']([^"\']*(?:xg|expected-goals)[^"\']*)["\']',

        # possession
        r'["\']([^"\']*possession[^"\']*)["\']',

        # corners
        r'["\']([^"\']*corner[^"\']*)["\']',

        # fetch
        r'fetch\(\s*["\']([^"\']+)["\']',

        # axios
        r'axios\.(?:get|post|put|delete)\(\s*["\']([^"\']+)["\']'
    ]


    for pattern in patterns:

        try:

            matches = re.findall(
                pattern,
                js,
                re.I
            )

            for match in matches:

                if isinstance(match, tuple):

                    for item in match:

                        if item:
                            results.add(item)

                else:

                    results.add(match)

        except Exception:
            pass


    return results


# ============================================================
# BUTON
# ============================================================

if st.button(
    "🎯 GERÇEK API ADAYLARINI BUL",
    type="primary"
):

    if not url:

        st.warning(
            "StatsHub URL'si gir."
        )

        st.stop()


    try:

        # ----------------------------------------------------
        # SAYFAYI AL
        # ----------------------------------------------------

        with st.spinner(
            "StatsHub sayfası indiriliyor..."
        ):

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )


        html = response.text


        st.success(
            f"HTTP {response.status_code}"
        )


        st.write(
            f"📄 HTML boyutu: "
            f"**{len(html):,} karakter**"
        )


        # ----------------------------------------------------
        # JS DOSYALARI
        # ----------------------------------------------------

        script_urls = find_script_urls(
            html,
            url
        )


        st.info(
            f"📜 **{len(script_urls)} JavaScript dosyası bulundu.**"
        )


        # ----------------------------------------------------
        # TARAMA
        # ----------------------------------------------------

        candidates = defaultdict(
            lambda: {
                "score": 0,
                "reasons": set(),
                "sources": set()
            }
        )


        progress = st.progress(0)


        downloaded = 0


        for index, js_url in enumerate(
            script_urls
        ):

            try:

                js_response = requests.get(
                    js_url,
                    headers=HEADERS,
                    timeout=20
                )


                if js_response.status_code != 200:

                    continue


                downloaded += 1


                js = js_response.text


                strings = extract_strings(
                    js
                )


                for value in strings:

                    value = value.strip()


                    if len(value) < 3:

                        continue


                    # Çok uzun JS parçalarını alma
                    if len(value) > 500:

                        continue


                    score, reasons = score_endpoint(
                        value
                    )


                    if score <= 0:

                        continue


                    candidates[value][
                        "score"
                    ] = max(
                        candidates[value]["score"],
                        score
                    )


                    for reason in reasons:

                        candidates[value][
                            "reasons"
                        ].add(reason)


                    candidates[value][
                        "sources"
                    ].add(js_url)


            except Exception:

                pass


            progress.progress(
                (index + 1)
                / len(script_urls)
            )


        # ----------------------------------------------------
        # SIRALA
        # ----------------------------------------------------

        ranked = []


        for value, info in candidates.items():

            ranked.append({

                "value":
                    value,

                "score":
                    info["score"],

                "reasons":
                    sorted(
                        info["reasons"]
                    ),

                "sources":
                    sorted(
                        info["sources"]
                    )
            })


        ranked.sort(
            key=lambda x: x["score"],
            reverse=True
        )


        # ----------------------------------------------------
        # SONUÇ
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🎯 EN GÜÇLÜ API / VERİ ADAYLARI"
        )


        col1, col2, col3 = st.columns(3)


        col1.metric(
            "JS dosyası",
            len(script_urls)
        )


        col2.metric(
            "İndirilen",
            downloaded
        )


        col3.metric(
            "Aday",
            len(ranked)
        )


        # ----------------------------------------------------
        # İLK 20
        # ----------------------------------------------------

        if not ranked:

            st.error(
                "API/veri adayı bulunamadı."
            )

        else:

            for index, item in enumerate(
                ranked[:20],
                1
            ):

                score = item[
                    "score"
                ]

                value = item[
                    "value"
                ]

                reasons = item[
                    "reasons"
                ]


                if score >= 70:

                    level = "🔥 ÇOK GÜÇLÜ"

                elif score >= 40:

                    level = "🟠 GÜÇLÜ"

                else:

                    level = "🟡 ZAYIF"


                with st.expander(
                    f"{index}. {level} | "
                    f"Skor {score} | "
                    f"{value[:120]}"
                ):

                    st.write(
                        "Bulunan adres/ifade:"
                    )

                    st.code(
                        value,
                        language="text"
                    )


                    st.write(
                        "Neden puan aldı:"
                    )

                    st.write(
                        ", ".join(
                            reasons
                        )
                    )


                    st.write(
                        "Bulunduğu JS dosyaları:"
                    )


                    for source in item[
                        "sources"
                    ]:

                        st.code(
                            source,
                            language="text"
                        )


        # ----------------------------------------------------
        # ÖZEL İSTATİSTİK ADAYLARI
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "📊 İSTATİSTİK ODAKLI ADAYLAR"
        )


        stat_words = [
            "statistics",
            "statistic",
            "shots",
            "xg",
            "possession",
            "corner",
            "lineup",
            "events"
        ]


        stat_candidates = []


        for item in ranked:

            low = item[
                "value"
            ].lower()


            if any(
                word in low
                for word in stat_words
            ):

                stat_candidates.append(
                    item
                )


        if stat_candidates:

            for item in stat_candidates[:30]:

                st.code(
                    item["value"],
                    language="text"
                )

        else:

            st.warning(
                "İstatistik adı içeren güçlü aday bulunamadı."
            )


        # ----------------------------------------------------
        # BİLGİ
        # ----------------------------------------------------

        st.divider()

        st.success(
            "✅ JavaScript taraması tamamlandı."
        )

        st.caption(
            "Bir sonraki aşamada en güçlü adaylardan "
            "gerçek JSON döndüren endpoint otomatik "
            "olarak test edilecek."
        )


    except Exception as e:

        st.error(
            "❌ Hata oluştu."
        )

        st.exception(e)
