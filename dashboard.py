import streamlit as st
import sqlite3
import json
import os
import pandas as pd

st.set_page_config(
    page_title="StatsHub Quant Engine",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ StatsHub Quant Engine")
st.caption("Model • Tahmin • Performans • Kalibrasyon")

DB_PATH = "data/database/quant_engine.db"
MODEL_PATH = "data/models/statshub_match_model.json"
REGISTRY_PATH = "data/models/model_registry.json"
CALIBRATION_PATH = "data/models/calibration.json"


def load_json(path):
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_connection():
    if not os.path.exists(DB_PATH):
        return None

    return sqlite3.connect(DB_PATH)


def get_tables(conn):
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """
    return pd.read_sql_query(query, conn)


def get_table_data(conn, table):
    try:
        return pd.read_sql_query(
            f'SELECT * FROM "{table}"',
            conn
        )
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})


# =========================================================
# DOSYA DURUMU
# =========================================================

st.subheader("🟢 Sistem Durumu")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Database",
        "OK" if os.path.exists(DB_PATH) else "YOK"
    )

with c2:
    st.metric(
        "Match Model",
        "OK" if os.path.exists(MODEL_PATH) else "YOK"
    )

with c3:
    st.metric(
        "Model Registry",
        "OK" if os.path.exists(REGISTRY_PATH) else "YOK"
    )

with c4:
    st.metric(
        "Calibration",
        "OK" if os.path.exists(CALIBRATION_PATH) else "YOK"
    )


# =========================================================
# MODEL
# =========================================================

st.divider()
st.subheader("🤖 Aktif Model")

registry = load_json(REGISTRY_PATH)
model = load_json(MODEL_PATH)
calibration = load_json(CALIBRATION_PATH)

if registry:

    active_model = registry.get("active_model", "Bilinmiyor")

    st.success(
        f"Aktif model: **{active_model}**"
    )

    models = registry.get("models", {})

    if active_model in models:

        m = models[active_model]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**Model Version**")
            st.write(m.get("model_version", active_model))

        with col2:
            st.write("**Home**")
            st.write(m.get("home", "-"))

        with col3:
            st.write("**Away**")
            st.write(m.get("away", "-"))

        col4, col5 = st.columns(2)

        with col4:
            st.metric(
                "λ Home",
                f"{m.get('lambda_home', 0):.3f}"
            )

        with col5:
            st.metric(
                "λ Away",
                f"{m.get('lambda_away', 0):.3f}"
            )

else:
    st.warning("Model registry bulunamadı.")


# =========================================================
# DATABASE
# =========================================================

st.divider()
st.subheader("🗄️ Quant Engine Database")

conn = get_connection()

if conn is None:

    st.error(
        f"Database bulunamadı: `{DB_PATH}`"
    )

else:

    tables = get_tables(conn)

    st.write(
        f"Database içindeki tablo sayısı: **{len(tables)}**"
    )

    if len(tables) > 0:

        selected_table = st.selectbox(
            "Tablo seç",
            tables["name"].tolist()
        )

        data = get_table_data(
            conn,
            selected_table
        )

        st.write(
            f"Satır sayısı: **{len(data)}**"
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "Database içinde tablo bulunamadı."
        )

    conn.close()


# =========================================================
# KALİBRASYON
# =========================================================

st.divider()
st.subheader("🧠 Model Kalibrasyonu")

if calibration:

    st.json(calibration)

else:

    st.info(
        "Henüz kalibrasyon verisi bulunmuyor."
    )


# =========================================================
# MODEL REGISTRY
# =========================================================

st.divider()
st.subheader("📚 Model Registry")

if registry:

    st.json(registry)

else:

    st.info(
        "Model registry bulunamadı."
    )


# =========================================================
# YENİLE
# =========================================================

st.divider()

if st.button(
    "🔄 Verileri Yenile",
    type="primary"
):

    st.rerun()
