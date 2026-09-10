import streamlit as st
import requests

st.set_page_config(
    page_title="StatsHub Quant Engine",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Quant Engine")

st.write(
    "StatsHub maç verilerini otomatik olarak çekmek "
    "ve daha sonra Quant analizine aktarmak için test sistemi."
)

st.divider()

st.subheader("📊 StatsHub Maç Verisi")

url = st.text_input(
    "StatsHub maç URL'sini gir:",
    placeholder="https://www.statshub.com/fixture/..."
)

if st.button("🔍 STATSHUB'A BAĞLAN", type="primary"):

    if not url:
        st.warning("Lütfen bir StatsHub maç URL'si gir.")

    elif "statshub.com/fixture/" not in url:
        st.error("Bu bir StatsHub maç URL'si gibi görünmüyor.")

    else:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 16; Mobile) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Mobile Safari/537.36"
            )
        }

        try:

            with st.spinner("StatsHub'a bağlanılıyor..."):

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30
                )

            st.success("✅ StatsHub sunucusuna bağlantı kuruldu.")

            st.divider()

            st.subheader("🔎 Bağlantı Sonucu")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "HTTP Status",
                    response.status_code
                )

            with col2:
                st.metric(
                    "Veri Boyutu",
                    f"{len(response.text):,} karakter"
                )

            with col3:
                st.metric(
                    "Content-Type",
                    response.headers.get(
                        "content-type",
                        "Bilinmiyor"
                    )
                )

            st.divider()

            html = response.text.lower()

            st.subheader("📋 StatsHub Bölüm Kontrolü")

            sections = {
                "Player Stats": "player stats",
                "Team Stats": "team stats",
                "Lineups": "lineups",
                "Trends": "trends",
                "Charts": "charts",
                "Opponent Stats": "opponent stats",
                "Match Ups": "match ups"
            }

            for name, keyword in sections.items():

                if keyword in html:
                    st.success(f"✅ {name} bulundu")
                else:
                    st.warning(f"⚠️ {name} HTML içinde bulunamadı")

            st.divider()

            st.subheader("🌐 Sayfa Başlığı")

            st.write(
                response.url
            )

            st.divider()

            st.subheader("🧪 Ham Veri Testi")

            with st.expander(
                "StatsHub'dan gelen ilk 3000 karakteri göster"
            ):
                st.code(
                    response.text[:3000],
                    language="html"
                )

        except requests.exceptions.Timeout:

            st.error(
                "❌ StatsHub bağlantısı zaman aşımına uğradı."
            )

        except requests.exceptions.RequestException as e:

            st.error(
                f"❌ Bağlantı hatası: {e}"
            )

        except Exception as e:

            st.error(
                f"❌ Beklenmeyen hata: {e}"
            )
