import streamlit as st
import requests

st.set_page_config(
    page_title="StatsHub Test",
    page_icon="⚽"
)

st.title("⚽ StatsHub Quant Engine")

url = st.text_input(
    "StatsHub URL",
    "https://www.statshub.com/fixture/psv-eindhoven-vs-shakhtar-donetsk-mtv02l/416477"
)

if st.button("TEST ET"):

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15
        )

        st.success(
            f"Bağlantı başarılı: HTTP {response.status_code}"
        )

        st.write(
            f"Sayfa uzunluğu: {len(response.text):,} karakter"
        )

    except Exception as e:
        st.error(f"Hata: {e}")
