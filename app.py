import pandas as pd
import streamlit as st

st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

st.title("🧺 Detector de Canastas Llenas")
st.caption("Prototipo de cross-selling por frecuencia de subrubros")

uploaded_file = st.file_uploader("Subí el CSV de ventas", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.success(f"Archivo cargado: {len(df):,} filas")

    required_cols = [
        "cliente_id",
        "RazonSocial",
        "subrubro",
        "articulo_codigo",
        "articulo_descripcion",
        "unidades",
        "importe"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Faltan columnas: {missing}")
        st.stop()

    clientes = sorted(df["RazonSocial"].dropna().unique())
    cliente_sel = st.selectbox("Seleccioná un cliente", clientes)

    df_cli = df[df["RazonSocial"] == cliente_sel]

    st.subheader("📦 Subrubros que compra")
    sub_freq = (
        df_cli.groupby("subrubro")["unidades"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    st.dataframe(sub_freq)

    st.subheader("💡 Sugerencias de venta cruzada (Top 5)")

    sub_cliente = set(df_cli["subrubro"])

    df_otros = df[~df["subrubro"].isin(sub_cliente)]

    sugerencias = (
        df_otros.groupby("subrubro")["unidades"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .reset_index()
    )

    st.dataframe(sugerencias)
else:
    st.info("Esperando que subas un archivo CSV")
