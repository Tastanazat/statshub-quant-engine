import streamlit as st
import requests
import re
from urllib.parse import urljoin

st.set_page_config(
    page_title="StatsHub Gerçek API Bulucu",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 StatsHub Gerçek API Bulucu")

st.info(
    "Amaç: StatsHub'ın maç istatistiklerini hangi gerçek veri/API çağrısından "
    "aldığını bulmak. Başka veri sağlayıcısı kullanılmaz."
)

url = st.text_input(
    "StatsHub maç URL'si",
    value="https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("🔍 GERÇEK API'Yİ BUL", type="primary"):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; K) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/140.0.0.0 Mobile Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9"
    }

    # ---------------------------------------------------------
    # 1 — ANA SAYFA
    # ---------------------------------------------------------

    st.subheader("1️⃣ StatsHub bağlantısı")

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        html = r.text

        st.success(f"HTTP {r.status_code}")
        st.write(f"HTML: **{len(html):,} karakter**")

    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        st.stop()

    # ---------------------------------------------------------
    # 2 — JAVASCRIPT DOSYALARINI BUL
    # ---------------------------------------------------------

    st.subheader("2️⃣ JavaScript dosyaları")

    script_urls = []

    scripts = re.findall(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        html,
        flags=re.I
    )

    for src in scripts:

        full_url = urljoin(url, src)

        if full_url not in script_urls:
            script_urls.append(full_url)

    st.write(
        f"Bulunan JS dosyası: **{len(script_urls)}**"
    )

    # ---------------------------------------------------------
    # 3 — JS İNDİR
    # ---------------------------------------------------------

    js_files = []

    progress = st.progress(0)

    for i, js_url in enumerate(script_urls):

        try:

            response = requests.get(
                js_url,
                headers=headers,
                timeout=20
            )

            if response.status_code == 200:

                js_files.append({
                    "url": js_url,
                    "text": response.text
                })

        except Exception:
            pass

        progress.progress(
            (i + 1) / max(len(script_urls), 1)
        )

    st.success(
        f"{len(js_files)} JS dosyası indirildi."
    )

    # ---------------------------------------------------------
    # 4 — GERÇEK NETWORK ÇAĞRILARINI ARA
    # ---------------------------------------------------------

    st.subheader("3️⃣ Network çağrıları")

    network_patterns = [

        r'fetch\s*\(',

        r'axios\.[a-zA-Z]+\s*\(',

        r'axios\s*\(',

        r'\.get\s*\(',

        r'\.post\s*\(',

        r'XMLHttpRequest',

        r'\.open\s*\(',

        r'graphql',

        r'baseURL',

        r'apiBase',

        r'apiUrl',

        r'API_URL',

        r'API_BASE'
    ]

    call_sites = []

    for js in js_files:

        text = js["text"]

        for pattern in network_patterns:

            matches = list(
                re.finditer(
                    pattern,
                    text,
                    flags=re.I
                )
            )

            for match in matches[:100]:

                start = max(
                    0,
                    match.start() - 700
                )

                end = min(
                    len(text),
                    match.end() + 1500
                )

                snippet = text[start:end]

                call_sites.append({
                    "type": pattern,
                    "url": js["url"],
                    "snippet": snippet
                })

    st.write(
        f"Network çağrısı bölgesi: **{len(call_sites)}**"
    )

    # ---------------------------------------------------------
    # 5 — NETWORK ÇAĞRILARININ İÇİNDEN STRING URL ÇIKAR
    # ---------------------------------------------------------

    st.subheader("4️⃣ Gerçek endpoint adayları")

    endpoint_candidates = []

    for item in call_sites:

        text = item["snippet"]

        # Tam URL
        full_urls = re.findall(
            r'["\'](https?://[^"\']+)["\']',
            text,
            flags=re.I
        )

        # /api/... yolları
        api_paths = re.findall(
            r'["\'](\/[^"\']{1,300})["\']',
            text,
            flags=re.I
        )

        for value in full_urls + api_paths:

            value = value.strip()

            # Çöp filtreleri
            low = value.lower()

            if len(value) < 5:
                continue

            if any(x in low for x in [
                ".css",
                ".woff",
                ".woff2",
                ".ttf",
                ".png",
                ".jpg",
                ".jpeg",
                ".svg",
                ".gif",
                "google",
                "facebook",
                "analytics",
                "sentry"
            ]):
                continue

            # Gerçek API ihtimali
            score = 0

            for word in [
                "/api/",
                "graphql",
                "fixture",
                "event",
                "statistics",
                "lineup",
                "player",
                "team",
                "match",
                "sport"
            ]:

                if word in low:
                    score += 1

            endpoint_candidates.append({
                "score": score,
                "value": value,
                "source": item["url"],
                "type": item["type"]
            })

    # Aynı endpointleri temizle
    unique = {}

    for item in endpoint_candidates:

        key = item["value"]

        if key not in unique:

            unique[key] = item

        elif item["score"] > unique[key]["score"]:

            unique[key] = item

    endpoint_candidates = list(unique.values())

    endpoint_candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    st.write(
        f"Filtre sonrası aday: **{len(endpoint_candidates)}**"
    )

    # ---------------------------------------------------------
    # 6 — EN GÜÇLÜ 50 ADAY
    # ---------------------------------------------------------

    for i, item in enumerate(
        endpoint_candidates[:50],
        1
    ):

        score = item["score"]

        if score >= 3:
            icon = "🔥"
        elif score >= 2:
            icon = "🟠"
        else:
            icon = "⚪"

        with st.expander(
            f"{icon} #{i} — Skor {score} — {item['value']}"
        ):

            st.write(
                "**Kaynak JS:**"
            )

            st.code(
                item["source"],
                language="text"
            )

            st.write(
                "**Network çağrısı:**"
            )

            st.code(
                item["type"],
                language="text"
            )

            st.write(
                "**Endpoint:**"
            )

            st.code(
                item["value"],
                language="text"
            )

    # ---------------------------------------------------------
    # 7 — STATSHUB MAÇ KİMLİKLERİNİ ARA
    # ---------------------------------------------------------

    st.subheader("5️⃣ Maç kimlikleri")

    ids = {
        "fixture": None,
        "eventId": None,
        "homeTeamId": None,
        "awayTeamId": None
    }

    patterns = {

        "fixture": r'"internalId"\s*:\s*(\d+)',

        "eventId": r'eventId["\']?\s*[:=]\s*["\']?(\d+)',

        "homeTeamId": r'homeTeamId["\']?\s*[:=]\s*["\']?(\d+)',

        "awayTeamId": r'awayTeamId["\']?\s*[:=]\s*["\']?(\d+)'
    }

    for name, pattern in patterns.items():

        match = re.search(
            pattern,
            html,
            flags=re.I
        )

        if match:
            ids[name] = match.group(1)

    for name, value in ids.items():

        st.write(
            f"**{name}:** {value if value else 'Bulunamadı'}"
        )

    # ---------------------------------------------------------
    # 8 — ÖNEMLİ KELİMELER
    # ---------------------------------------------------------

    st.subheader("6️⃣ İstatistik fonksiyonları")

    important = [
        "showMatchStats",
        "playerStats",
        "teamStats",
        "matchStats",
        "statistics",
        "lineups",
        "shots",
        "xg",
        "possession",
        "corners",
        "goals",
        "passes"
    ]

    found = {}

    for word in important:

        count = 0

        for js in js_files:

            count += len(
                re.findall(
                    re.escape(word),
                    js["text"],
                    flags=re.I
                )
            )

        found[word] = count

    for word, count in found.items():

        st.write(
            f"**{word}:** {count}"
        )

    # ---------------------------------------------------------
    # SONUÇ
    # ---------------------------------------------------------

    st.divider()

    st.subheader("🎯 Sonuç")

    if endpoint_candidates:

        st.success(
            "API çağrısı için adaylar bulundu. "
            "En yüksek skorlu sonuçları inceleyeceğiz."
        )

    else:

        st.warning(
            "Statik JS taramasında doğrudan endpoint bulunamadı."
        )

    st.info(
        "Bir sonraki aşamada en güçlü adayları otomatik olarak "
        "HTTP ile test edip JSON döndüren StatsHub endpointini "
        "bulacağız."
    )            r = requests.get(
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
