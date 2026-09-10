import streamlit as st
import requests
import re
from urllib.parse import urljoin


# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="StatsHub Endpoint Discovery",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 StatsHub Endpoint Discovery")

st.write(
    "Bu araç StatsHub sayfasının kullandığı API, JSON ve veri "
    "adreslerini otomatik olarak araştırır."
)

st.info(
    "⚠️ Bu aşamada tahmin yapılmaz. Amaç gerçek StatsHub "
    "verisinin nereden geldiğini bulmaktır."
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
# API / ENDPOINT TARAMA
# ============================================================

if st.button(
    "🔎 API / VERİ ENDPOINTLERİNİ BUL",
    type="primary"
):

    if not url:

        st.warning("Önce StatsHub URL'si gir.")
        st.stop()

    try:

        headers = {

            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
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


        # ====================================================
        # SAYFAYI ÇEK
        # ====================================================

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
            f"📄 HTML boyutu: "
            f"**{len(html):,} karakter**"
        )


        # ====================================================
        # 1 — TÜM HTTP/HTTPS URL'LERİ
        # ====================================================

        absolute_urls = re.findall(
            r'https?://[^\s"\'<>\\]+',
            html
        )


        # Temizle
        cleaned_urls = set()

        for item in absolute_urls:

            item = item.rstrip(
                ".,);]}>'\""
            )

            if len(item) > 10:
                cleaned_urls.add(item)


        # ====================================================
        # 2 — /api/... ADRESLERİ
        # ====================================================

        api_paths = re.findall(
            r'["\'](\/api\/[^"\']+)["\']',
            html,
            re.I
        )


        # ====================================================
        # 3 — JSON ADRESLERİ
        # ====================================================

        json_paths = re.findall(
            r'["\']([^"\']+\.json(?:\?[^"\']*)?)["\']',
            html,
            re.I
        )


        # ====================================================
        # 4 — API KELİMESİ GEÇEN ADRESLER
        # ====================================================

        api_urls = set()

        for item in cleaned_urls:

            if (
                "/api/" in item.lower()
                or "api." in item.lower()
                or "graphql" in item.lower()
            ):

                api_urls.add(item)


        for item in api_paths:

            api_urls.add(
                urljoin(
                    url,
                    item
                )
            )


        # ====================================================
        # 5 — FUTBOL VERİSİYLE İLGİLİ ADRESLER
        # ====================================================

        football_keywords = [

            "fixture",
            "event",
            "statistics",
            "statistic",
            "lineup",
            "player",
            "team",
            "shot",
            "goal",
            "corner",
            "xg",
            "possession",
            "momentum",
            "match",
            "incidents",
            "formation",
            "performance",
            "trend",
            "opponent"
        ]


        football_urls = set()

        all_possible = (
            list(cleaned_urls)
            + list(api_urls)
            + [
                urljoin(url, x)
                for x in api_paths
            ]
            + json_paths
        )


        for item in all_possible:

            low = item.lower()

            if any(
                keyword in low
                for keyword in football_keywords
            ):

                football_urls.add(item)


        # ====================================================
        # SONUÇLAR
        # ====================================================

        st.divider()

        st.subheader(
            "📊 Endpoint Keşif Sonucu"
        )


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "HTTP URL",
            len(cleaned_urls)
        )

        col2.metric(
            "API URL",
            len(api_urls)
        )

        col3.metric(
            "Futbol Veri URL",
            len(football_urls)
        )


        # ====================================================
        # API ADRESLERİ
        # ====================================================

        st.divider()

        st.subheader(
            "🔌 API / GraphQL Adresleri"
        )

        if api_urls:

            for i, item in enumerate(
                sorted(api_urls),
                1
            ):

                st.code(
                    item,
                    language="text"
                )

        else:

            st.warning(
                "HTML içinde açık bir /api/ adresi bulunamadı."
            )


        # ====================================================
        # FUTBOL VERİ ADRESLERİ
        # ====================================================

        st.divider()

        st.subheader(
            "⚽ Futbol Verisiyle İlgili Adresler"
        )

        if football_urls:

            for i, item in enumerate(
                sorted(football_urls),
                1
            ):

                st.code(
                    item,
                    language="text"
                )

        else:

            st.warning(
                "Futbol veri endpointi bulunamadı."
            )


        # ====================================================
        # JSON DOSYALARI
        # ====================================================

        st.divider()

        st.subheader(
            "📦 JSON Adresleri"
        )

        if json_paths:

            unique_json = sorted(
                set(json_paths)
            )

            for item in unique_json:

                st.code(
                    item,
                    language="text"
                )

        else:

            st.info(
                "Açık JSON dosya adresi bulunamadı."
            )


        # ====================================================
        # İLGİLİ HTML SATIRLARI
        # ====================================================

        st.divider()

        st.subheader(
            "🧩 Veri Anahtarları Bulundu mu?"
        )

        search_terms = [

            "/api/",
            "graphql",
            "statistics",
            "lineup",
            "player",
            "fixture",
            "shots",
            "xg",
            "possession",
            "events"
        ]


        found_terms = []

        html_lower = html.lower()

        for term in search_terms:

            count = html_lower.count(
                term.lower()
            )

            if count > 0:

                found_terms.append(
                    (term, count)
                )


        for term, count in found_terms:

            st.write(
                f"**{term}** → {count} kez"
            )


        # ====================================================
        # HAM API İPUÇLARI
        # ====================================================

        st.divider()

        st.subheader(
            "🔬 JavaScript Veri İpuçları"
        )

        patterns = [

            r'fetch\((.*?)\)',

            r'axios\.(get|post)\((.*?)\)',

            r'XMLHttpRequest',

            r'graphql',

            r'query\s*:',

            r'endpoint',

            r'baseURL',

            r'apiUrl',

            r'api_url'
        ]


        found_patterns = []

        for pattern in patterns:

            matches = re.findall(
                pattern,
                html,
                re.I | re.S
            )

            if matches:

                found_patterns.append(
                    (
                        pattern,
                        len(matches)
                    )
                )


        if found_patterns:

            for pattern, count in found_patterns:

                st.write(
                    f"`{pattern}` → "
                    f"**{count}** eşleşme"
                )

        else:

            st.info(
                "Açık JavaScript API çağrısı bulunamadı."
            )


        # ====================================================
        # ÖNEMLİ NOT
        # ====================================================

        st.divider()

        st.success(
            "✅ Endpoint taraması tamamlandı."
        )

        st.caption(
            "Sonraki aşamada bulunan gerçek endpointleri "
            "tek tek test ederek hangi endpointin maç "
            "istatistiklerini döndürdüğünü belirleyeceğiz."
        )


    except Exception as e:

        st.error(
            "❌ Bir hata oluştu."
        )

        st.exception(e)
