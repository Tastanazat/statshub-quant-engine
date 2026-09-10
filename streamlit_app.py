
import streamlit as st

st.set_page_config(
    page_title="StatsHub Quant Engine",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Quant Engine")

st.write(
    "StatsHub maç verilerini çekmek ve Quant analizine hazırlamak için "
    "yeni sistem."
)

st.divider()

st.subheader("📊 StatsHub Maç Verisi")

url = st.text_input(
    "StatsHub maç URL'sini gir:",
    placeholder="https://www.statshub.com/fixture/..."
)

if st.button("🔍 VERİLERİ ÇEK", type="primary"):

    if not url:
        st.warning("Lütfen bir StatsHub maç URL'si gir.")
    else:
        st.info("URL alındı. Veri çekme modülü bir sonraki aşamada eklenecek.")

        st.write("Girilen URL:")
        st.code(url)
