import streamlit as st
import requests
import re
from urllib.parse import urljoin


# ============================================================
# SAYFA
# ============================================================

st.set_page_config(
    page_title="StatsHub JS API Discovery",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 StatsHub JavaScript API Discovery")

st.write(
    "StatsHub sayfasının JavaScript dosyalarını tarar ve "
    "maç verisinin çağrıldığı olası endpointleri bulur."
)

st.info(
    "⚠️ Bu aşamada tahmin yapılmaz. "
    "Amaç yalnızca StatsHub veri kaynağını bulmaktır."
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
# HTTP AYARLARI
# ============================================================

headers = {
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
# SCRIPT URL'LERİNİ BUL
# ============================================================

def find_script_urls(html, page_url):

    results = set()

    pattern = re.compile(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        re.I
    )

    matches = pattern.findall(html)

    for src in matches:

        full_url = urljoin(
            page_url,
            src
        )

        results.add(full_url)

    return sorted(results)


# ============================================================
# JAVASCRIPT İÇERİĞİNDE API İPUÇLARINI BUL
# ============================================================

def find_api_candidates(js):

    results = set()

    patterns = [

        # /api/...
        r'["\']([^"\']*/api/[^"\']+)["\']',

        # absolute https URLs
        r'["\'](https?://[^"\']+)["\']',

        # fetch("...")
        r'fetch\s*\(\s*["\']([^"\']+)["\']',

        # axios.get("...")
        r'axios\.(?:get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',

        # graphql
        r'["\']([^"\']*graphql[^"\']*)["\']',

        # fixture paths
        r'["\']([^"\']*fixture[^"\']*)["\']',

        # statistics
        r'["\']([^"\']*(?:statistics|statistic)[^"\']*)["\']',

        # lineup
        r'["\']([^"\']*lineup[^"\']*)["\']',

        # player
        r'["\']([^"\']*player[^"\']*)["\']',

        # events
        r'["\']([^"\']*(?:events|event)[^"\']*)["\']',

        # shots
        r'["\']([^"\']*shots[^"\']*)["\']',

        # xg
        r'["\']([^"\']*(?:xg|expected-goals)[^"\']*)["\']'
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

                    for value in match:

                        if value:
                            results.add(value)

                else:

                    results.add(match)

        except Exception:
            pass


    return results


# ============================================================
# ANA İŞLEM
# ============================================================

if st.button(
    "🚀 JAVASCRIPT DOSYALARINI TARA",
    type="primary"
):

    if not url:

        st.warning(
            "StatsHub URL'si girmen gerekiyor."
        )

        st.stop()


    try:

        # ----------------------------------------------------
        # SAYFAYI İNDİR
        # ----------------------------------------------------

        with st.spinner(
            "StatsHub sayfası indiriliyor..."
        ):

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )


        st.success(
            f"HTTP {response.status_code}"
        )


        html = response.text


        st.write(
            f"📄 HTML: "
            f"**{len(html):,} karakter**"
        )


        # ----------------------------------------------------
        # SCRIPT DOSYALARINI BUL
        # ----------------------------------------------------

        script_urls = find_script_urls(
            html,
            url
        )


        st.divider()

        st.subheader(
            "📜 JavaScript Dosyaları"
        )


        st.metric(
            "Bulunan JS dosyası",
            len(script_urls)
        )


        if not script_urls:

            st.error(
                "JavaScript dosyası bulunamadı."
            )

            st.stop()


        # ----------------------------------------------------
        # JS LİSTESİ
        # ----------------------------------------------------

        for i, js_url in enumerate(
            script_urls,
            1
        ):

            st.code(
                f"{i}. {js_url}",
                language="text"
            )


        # ----------------------------------------------------
        # JS DOSYALARINI İNDİR
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "⬇️ JavaScript Analizi"
        )


        all_candidates = set()

        downloaded = 0


        progress = st.progress(0)


        for index, js_url in enumerate(
            script_urls
        ):

            try:

                js_response = requests.get(
                    js_url,
                    headers=headers,
                    timeout=20
                )


                if js_response.status_code != 200:

                    continue


                js = js_response.text

                downloaded += 1


                candidates = find_api_candidates(
                    js
                )


                for candidate in candidates:

                    all_candidates.add(
                        (
                            js_url,
                            candidate
                        )
                    )


            except Exception:

                pass


            progress.progress(
                (index + 1)
                / len(script_urls)
            )


        # ----------------------------------------------------
        # SONUÇ
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🎯 Bulunan Olası Veri Endpointleri"
        )


        st.write(
            f"Başarıyla indirilen JS: "
            f"**{downloaded} / {len(script_urls)}**"
        )


        # ----------------------------------------------------
        # KATEGORİLER
        # ----------------------------------------------------

        categories = {

            "STATISTICS": [],
            "FIXTURE": [],
            "LINEUP": [],
            "PLAYER": [],
            "EVENTS": [],
            "SHOTS": [],
            "XG": [],
            "GRAPHQL": [],
            "OTHER": []
        }


        for js_url, candidate in all_candidates:

            low = candidate.lower()


            if (
                "statistics" in low
                or "statistic" in low
            ):

                categories[
                    "STATISTICS"
                ].append(
                    (js_url, candidate)
                )


            elif "lineup" in low:

                categories[
                    "LINEUP"
                ].append(
                    (js_url, candidate)
                )


            elif "player" in low:

                categories[
                    "PLAYER"
                ].append(
                    (js_url, candidate)
                )


            elif (
                "shots" in low
            ):

                categories[
                    "SHOTS"
                ].append(
                    (js_url, candidate)
                )


            elif (
                "xg" in low
                or "expected-goals" in low
            ):

                categories[
                    "XG"
                ].append(
                    (js_url, candidate)
                )


            elif (
                "events" in low
                or "/event" in low
            ):

                categories[
                    "EVENTS"
                ].append(
                    (js_url, candidate)
                )


            elif (
                "fixture" in low
                or "match" in low
            ):

                categories[
                    "FIXTURE"
                ].append(
                    (js_url, candidate)
                )


            elif "graphql" in low:

                categories[
                    "GRAPHQL"
                ].append(
                    (js_url, candidate)
                )


            elif "/api/" in low:

                categories[
                    "OTHER"
                ].append(
                    (js_url, candidate)
                )


            else:

                categories[
                    "OTHER"
                ].append(
                    (js_url, candidate)
                )


        # ----------------------------------------------------
        # ÖZET
        # ----------------------------------------------------

        cols = st.columns(4)

        cols[0].metric(
            "Toplam aday",
            len(all_candidates)
        )

        cols[1].metric(
            "Statistics",
            len(categories["STATISTICS"])
        )

        cols[2].metric(
            "Player",
            len(categories["PLAYER"])
        )

        cols[3].metric(
            "Fixture",
            len(categories["FIXTURE"])
        )


        # ----------------------------------------------------
        # ÖNEMLİ KATEGORİLERİ GÖSTER
        # ----------------------------------------------------

        important_categories = [

            "STATISTICS",
            "FIXTURE",
            "LINEUP",
            "PLAYER",
            "EVENTS",
            "SHOTS",
            "XG",
            "GRAPHQL"
        ]


        for category in important_categories:

            items = categories[
                category
            ]

            if not items:
                continue


            st.divider()

            st.subheader(
                f"⚽ {category}"
            )


            # Aynı endpointleri temizle
            unique_items = sorted(
                set(items),
                key=lambda x: x[1]
            )


            for js_url, candidate in unique_items[:50]:

                with st.expander(
                    candidate[:180]
                ):

                    st.write(
                        "Kaynak JavaScript:"
                    )

                    st.code(
                        js_url,
                        language="text"
                    )

                    st.write(
                        "Bulunan ifade:"
                    )

                    st.code(
                        candidate,
                        language="text"
                    )


        # ----------------------------------------------------
        # TÜM ADAYLAR
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "🧩 Tüm API Adayları"
        )


        with st.expander(
            "Tüm sonuçları göster"
        ):

            for js_url, candidate in sorted(
                all_candidates,
                key=lambda x: x[1]
            ):

                st.write(
                    candidate
                )


        # ----------------------------------------------------
        # SONUÇ
        # ----------------------------------------------------

        st.divider()

        if categories["STATISTICS"]:

            st.success(
                "🎯 Statistics ile ilgili endpoint "
                "adayları bulundu!"
            )

        elif categories["FIXTURE"]:

            st.warning(
                "Fixture endpointleri bulundu fakat "
                "statistics endpointi henüz doğrulanmadı."
            )

        else:

            st.warning(
                "Açık bir istatistik endpointi bulunamadı."
            )


        st.info(
            "📌 Sonraki aşamada bulduğumuz adayları "
            "doğrudan HTTP ile test edip hangisinin "
            "gerçek JSON maç verisi döndürdüğünü "
            "belirleyeceğiz."
        )


    except Exception as e:

        st.error(
            "❌ Hata oluştu."
        )

        st.exception(e)
