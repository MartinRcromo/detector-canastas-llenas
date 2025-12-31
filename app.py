# app.py — Detector de Canastas Llenas (Puntos 1–4)
# Streamlit Cloud: main file = app.py
# Reqs: streamlit, pandas, numpy

import io
import re
import pandas as pd
import numpy as np
import streamlit as st


# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

TITLE = "🧺 Detector de Canastas Llenas"
SUBTITLE = "Prototipo de cross-selling por frecuencia / co-ocurrencia de subrubros (por cliente)."


# -----------------------------
# Helpers: lectura + normalización
# -----------------------------
def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace("$", "", regex=False)
    )
    return df


def _to_number(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False).str.replace(" ", "", regex=False)

    mask_comma = s.str.contains(",", regex=False)
    s.loc[mask_comma] = (
        s.loc[mask_comma]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    s.loc[~mask_comma] = s.loc[~mask_comma].str.replace(",", "", regex=False)

    s = s.str.replace(r"[^\d\.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def read_any_table(uploaded_file) -> pd.DataFrame:
    """Lee CSV/Excel con fallback de encoding y separador."""
    name = (uploaded_file.name or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
        return _normalize_columns(df)

    raw = uploaded_file.getvalue()
    # IMPORTANT: utf-8-sig primero para archivos con BOM
    encodings = ["utf-8-sig", "utf-8", "latin1", "utf-16"]
    seps = [";", ",", "\t", "|"]

    last_err = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc)
                if df.shape[1] <= 1:
                    continue
                return _normalize_columns(df)
            except Exception as e:
                last_err = e
                continue
    raise RuntimeError(f"No pude leer el archivo. Último error: {last_err}")


REQUIRED = {
    "cliente": ["cliente", "razonsocial", "razon_social", "razon", "cliente_nombre"],
    "cliente_id": ["cliente_id", "cliente_codigo", "codigo_cliente", "id_cliente"],
    "cuit": ["cuit", "cuit_cliente", "tax_id"],
    "subrubro": ["subrubro", "articulo_sub_rubro", "articulo_subrubro", "sub_rubro", "subrubros"],
    "importe": ["importe", "importe_", "importe__"],
    "unidades": ["unidades", "unidad", "qty", "cantidad"],
    "cant_pedidos": ["cant_pedidos", "cantidad_pedidos", "cant_pedido", "pedidos"],
    "localidad": ["localidad", "ciudad", "zona", "localidad_cliente"],
    "vendedor": ["vendedor", "zona_comercial", "ejecutivo", "seller"],
    "anio_mes": ["anio_mes", "año_mes", "periodo", "mes", "year_month"],
    "articulo_codigo": ["articulo_codigo", "articulo_cod", "codigo_articulo", "sku", "articulo"],
    "articulo_descripcion": ["articulo_descripcion", "descripcion", "articulo_desc", "producto"],
    "empresa": ["empresa", "compania", "unidad_de_negocio"],
}


def pick_col(df_cols, candidates):
    for c in candidates:
        if c in df_cols:
            return c
    return None


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = set(df.columns)

    mapping = {}
    for std_name, candidates in REQUIRED.items():
        col = pick_col(cols, candidates)
        if col:
            mapping[std_name] = col

    if "subrubro" not in mapping:
        raise ValueError("Falta columna de subrubro (ej: 'subrubro' o 'Articulo Sub Rubro').")

    if "cliente" not in mapping and "cliente_id" not in mapping:
        raise ValueError("Falta columna de cliente (ej: 'RazonSocial' o 'cliente_id').")

    df = df.rename(columns={v: k for k, v in mapping.items()})

    # Completar cliente si viene solo id
    if "cliente" not in df.columns and "cliente_id" in df.columns:
        df["cliente"] = df["cliente_id"].astype(str)

    # Limpieza básica
    df["cliente"] = df["cliente"].astype(str).str.strip()
    df["subrubro"] = df["subrubro"].astype(str).str.strip()

    # Numéricos
    df["importe"] = _to_number(df.get("importe", pd.Series([0] * len(df)))).fillna(0.0)
    df["unidades"] = _to_number(df.get("unidades", pd.Series([0] * len(df)))).fillna(0.0)
    df["cant_pedidos"] = _to_number(df.get("cant_pedidos", pd.Series([1] * len(df)))).fillna(1.0)

    # anio_mes si existe: mantener como string sortable tipo YYYYMM o YYYY-MM
    if "anio_mes" in df.columns:
        df["anio_mes"] = df["anio_mes"].astype(str).str.strip()

    # Filtrar vacíos
    df = df[df["cliente"].ne("") & df["subrubro"].ne("")]
    return df


def fmt_int(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def fmt_money(n: float) -> str:
    # sin símbolo para evitar confusiones de moneda
    return f"{float(n):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


# -----------------------------
# Modelo (cache)
# -----------------------------
@st.cache_data(show_spinner=False)
def build_model(df: pd.DataFrame):
    # Agregado cliente-subrubro
    agg_cs = df.groupby(["cliente", "subrubro"], as_index=False).agg(
        cant_pedidos=("cant_pedidos", "sum"),
        unidades=("unidades", "sum"),
        importe=("importe", "sum"),
    )

    # Matriz compras por cliente (binaria)
    pivot_pedidos = agg_cs.pivot_table(
        index="cliente",
        columns="subrubro",
        values="cant_pedidos",
        aggfunc="sum",
        fill_value=0.0,
    )
    X_bin = (pivot_pedidos > 0).astype(int).values

    # Co-ocurrencia subrubro-subrubro
    co = pd.DataFrame(X_bin.T @ X_bin, index=pivot_pedidos.columns, columns=pivot_pedidos.columns)

    # Frecuencia global
    freq = pivot_pedidos.sum(axis=0).sort_values(ascending=False)

    # Productos por subrubro (si existen columnas)
    has_products = ("articulo_descripcion" in df.columns) or ("articulo_codigo" in df.columns)
    return agg_cs, pivot_pedidos, co, freq, has_products


def recommend_for_client(client: str, pivot: pd.DataFrame, co: pd.DataFrame, freq: pd.Series, topk=10):
    if client not in pivot.index:
        return pd.DataFrame(columns=["subrubro", "score_cooc", "freq_global"])

    owned = pivot.loc[client]
    bought = owned[owned > 0].index.tolist()
    not_bought = owned[owned == 0].index.tolist()

    if len(bought) == 0:
        rec = freq.head(topk).reset_index()
        rec.columns = ["subrubro", "freq_global"]
        rec["score_cooc"] = np.nan
        return rec[["subrubro", "score_cooc", "freq_global"]]

    scores = co.loc[not_bought, bought].sum(axis=1)
    rec = pd.DataFrame(
        {
            "subrubro": scores.index,
            "score_cooc": scores.values,
            "freq_global": freq.reindex(scores.index).fillna(0).values,
        }
    ).sort_values(["score_cooc", "freq_global"], ascending=False)

    return rec.head(topk)


def recommend_for_subrubro(subrubro: str, co: pd.DataFrame, freq: pd.Series, topk=10):
    if subrubro not in co.index:
        return pd.DataFrame(columns=["subrubro", "score_cooc", "freq_global"])
    scores = co.loc[subrubro].drop(index=subrubro).sort_values(ascending=False).head(topk)
    rec = pd.DataFrame(
        {"subrubro": scores.index, "score_cooc": scores.values, "freq_global": freq.reindex(scores.index).fillna(0).values}
    )
    return rec


def metric_col_name(rank_metric: str) -> str:
    # rank_metric: "importe" | "unidades" | "pedidos"
    return {"importe": "importe", "unidades": "unidades", "pedidos": "cant_pedidos"}[rank_metric]


# -----------------------------
# UI
# -----------------------------
st.title(TITLE)
st.caption(SUBTITLE)

with st.sidebar:
    st.header("Datos")
    uploaded = st.file_uploader("Subí tu archivo (CSV/Excel)", type=["csv", "xlsx", "xls"])
    st.divider()
    st.caption("Tip: si el CSV viene de Excel, probá ';' como separador (este loader lo detecta).")

if uploaded is None:
    st.info("Subí un archivo para empezar.")
    st.stop()

try:
    df_raw = read_any_table(uploaded)
except Exception as e:
    st.error(str(e))
    st.stop()

try:
    df = standardize(df_raw)
except Exception as e:
    st.error(f"No pude interpretar columnas: {e}")
    st.write("Columnas detectadas:", list(df_raw.columns))
    st.stop()

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Filas", fmt_int(len(df)))
c2.metric("Clientes", fmt_int(df["cliente"].nunique()))
c3.metric("Subrubros", fmt_int(df["subrubro"].nunique()))

with st.spinner("Armando modelo..."):
    agg_cs, pivot, co, freq, has_products = build_model(df)

st.divider()

# Tabs (Punto 1+2) / (Punto 3)  — Punto 4 vive dentro del tab cliente
tab_cliente, tab_subrubro = st.tabs(["🔎 Por cliente (Punto 1 + 2 + 4)", "🧭 Por subrubro (Punto 3)"])


# -----------------------------
# TAB CLIENTE (Punto 1 + 2 + 4)
# -----------------------------
with tab_cliente:
    st.subheader("Buscar cliente")

    # Construir “etiqueta” cliente con posibles IDs/CUIT
    base = df[["cliente"]].drop_duplicates().copy()
    if "cliente_id" in df.columns:
        base = base.merge(df[["cliente", "cliente_id"]].drop_duplicates(), on="cliente", how="left")
    else:
        base["cliente_id"] = ""

    if "cuit" in df.columns:
        base = base.merge(df[["cliente", "cuit"]].drop_duplicates(), on="cliente", how="left")
    else:
        base["cuit"] = ""

    def make_label(r):
        parts = [str(r["cliente"]).strip()]
        if str(r.get("cliente_id", "")).strip():
            parts.append(f"ID {str(r['cliente_id']).strip()}")
        if str(r.get("cuit", "")).strip() and str(r.get("cuit", "")).strip().lower() != "nan":
            parts.append(f"CUIT {str(r['cuit']).strip()}")
        return " | ".join(parts)

    base["label"] = base.apply(make_label, axis=1)

    # BUSCADOR (Punto 1)
    q = st.text_input("Buscar por Razón Social / Código Cliente / CUIT", value="", placeholder="Ej: fridman, 167, 20-211...")
    q_norm = q.strip().lower()

    if q_norm:
        mask = base["label"].str.lower().str.contains(re.escape(q_norm), na=False)
        options = base.loc[mask, "label"].tolist()
        if not options:
            st.warning("No encontré clientes con ese texto. Probá con otra parte del nombre, el ID o el CUIT.")
    else:
        options = base["label"].tolist()

    selected_label = st.selectbox("Seleccioná un cliente", options=options, index=0 if options else None)

    if not selected_label:
        st.stop()

    # Resolver cliente real desde label
    selected_cliente = selected_label.split("|")[0].strip()

    # Paneles
    left, right = st.columns([1.1, 0.9], gap="large")

    # Tabla subrubros cliente
    with left:
        st.markdown("### 📦 Subrubros que compra")
        sub = (
            agg_cs[agg_cs["cliente"] == selected_cliente]
            .groupby("subrubro", as_index=False)
            .agg(
                cant_pedidos=("cant_pedidos", "sum"),
                unidades=("unidades", "sum"),
                importe=("importe", "sum"),
            )
            .sort_values("importe", ascending=False)
        )

        # Formateo amigable
        sub_show = sub.copy()
        sub_show["importe"] = sub_show["importe"].map(fmt_money)
        sub_show["unidades"] = sub_show["unidades"].round(0).astype(int)
        sub_show["cant_pedidos"] = sub_show["cant_pedidos"].round(0).astype(int)
        sub_show = sub_show.rename(columns={"cant_pedidos": "pedidos"})

        st.dataframe(sub_show, use_container_width=True, height=420)

    # Sugerencias + Productos (Punto 2) + Plan de acción (Punto 4)
    with right:
        st.markdown("### 💡 Sugerencias de Venta Cruzada (Top 10) + Productos (Punto 2)")

        rank_metric = st.radio(
            "¿Cómo querés rankear los productos dentro de cada subrubro?",
            ["importe", "unidades", "pedidos"],
            index=0,
            horizontal=True,
        )
        top_subrubros = st.slider("Cantidad de subrubros oportunidad", min_value=3, max_value=25, value=10, step=1)
        top_products = st.slider("Productos por subrubro", min_value=3, max_value=20, value=10, step=1)

        rec = recommend_for_client(selected_cliente, pivot, co, freq, topk=top_subrubros)

        rec_show = rec.copy()
        # score puede ser grande: mantener numérico
        rec_show["score_cooc"] = rec_show["score_cooc"].fillna(0).astype(int)
        rec_show["freq_global"] = rec_show["freq_global"].fillna(0).astype(int)

        st.dataframe(rec_show.rename(columns={"score_cooc": "score_similitud"}), use_container_width=True, height=260)

        # -----------------------------
        # PUNTO 4: Plan de acción por subrubro recomendado
        # -----------------------------
        st.markdown("### 🧠 Plan de acción (Punto 4)")
        st.caption("Sin venta por operación, armamos el plan con **ranking por importe/unidades/pedidos** y (si existe) **anio_mes** como “último mes / tendencia”.")

        if not has_products:
            st.info("Para el Punto 4 necesito columnas de producto (articulo_descripcion y/o articulo_codigo). En tu CSV no aparecen.")
        else:
            metric_col = metric_col_name(rank_metric)

            # Data base solo del cliente, para sacar “último mes” si existe
            df_cliente = df[df["cliente"] == selected_cliente].copy()

            # Si hay anio_mes, limpiar a algo comparable (YYYYMM)
            has_period = "anio_mes" in df.columns

            def normalize_period(s: str) -> str:
                s = (s or "").strip()
                # acepta YYYY-MM, YYYY/MM, YYYYMM
                s = s.replace("/", "-")
                m = re.match(r"^(\d{4})-(\d{1,2})$", s)
                if m:
                    y, mo = m.group(1), int(m.group(2))
                    return f"{y}{mo:02d}"
                m2 = re.match(r"^(\d{6})$", s)
                if m2:
                    return s
                # fallback: solo dígitos
                digs = re.sub(r"\D", "", s)
                if len(digs) == 6:
                    return digs
                return s

            if has_period:
                df_cliente["anio_mes_norm"] = df_cliente["anio_mes"].map(normalize_period)
                df["anio_mes_norm"] = df["anio_mes"].map(normalize_period)

            # Para cada subrubro recomendado, sugerir productos top
            for _, row in rec.head(top_subrubros).iterrows():
                sr = row["subrubro"]
                score = int(row["score_cooc"]) if pd.notna(row["score_cooc"]) else 0

                with st.expander(f"📌 {sr}  — score {score}", expanded=False):
                    cols_group = ["subrubro"]
                    if "articulo_codigo" in df.columns:
                        cols_group.append("articulo_codigo")
                    if "articulo_descripcion" in df.columns:
                        cols_group.append("articulo_descripcion")

                    dfx = df[df["subrubro"] == sr].copy()

                    # Agregado por producto
                    g = (
                        dfx.groupby(cols_group, as_index=False)
                        .agg(
                            importe=("importe", "sum"),
                            unidades=("unidades", "sum"),
                            pedidos=("cant_pedidos", "sum"),
                        )
                        .sort_values(metric_col, ascending=False)
                        .head(top_products)
                    )

                    # Si hay periodo, sumar "ultimo_mes"
                    if has_period and "anio_mes_norm" in dfx.columns:
                        last = (
                            dfx.groupby(cols_group, as_index=False)["anio_mes_norm"]
                            .max()
                            .rename(columns={"anio_mes_norm": "ultimo_mes"})
                        )
                        g = g.merge(last, on=cols_group, how="left")

                    # Formateo
                    g_show = g.copy()
                    if "importe" in g_show.columns:
                        g_show["importe"] = g_show["importe"].map(fmt_money)
                    g_show["unidades"] = g_show["unidades"].round(0).astype(int)
                    g_show["pedidos"] = g_show["pedidos"].round(0).astype(int)

                    # Orden columnas lindo
                    ordered = []
                    if "articulo_codigo" in g_show.columns:
                        ordered.append("articulo_codigo")
                    if "articulo_descripcion" in g_show.columns:
                        ordered.append("articulo_descripcion")
                    ordered += ["importe", "unidades", "pedidos"]
                    if "ultimo_mes" in g_show.columns:
                        ordered.append("ultimo_mes")

                    st.dataframe(g_show[ordered], use_container_width=True, height=260)

                    # Mini insight de tendencia (si existe anio_mes)
                    if has_period:
                        st.caption("📈 Tendencia mensual (subrubro recomendado)")
                        by_m = (
                            dfx.groupby("anio_mes_norm", as_index=False)
                            .agg(importe=("importe", "sum"), unidades=("unidades", "sum"), pedidos=("cant_pedidos", "sum"))
                            .sort_values("anio_mes_norm", ascending=True)
                            .tail(12)
                        )
                        by_m_show = by_m.copy()
                        by_m_show["importe"] = by_m_show["importe"].map(fmt_money)
                        by_m_show["unidades"] = by_m_show["unidades"].round(0).astype(int)
                        by_m_show["pedidos"] = by_m_show["pedidos"].round(0).astype(int)
                        by_m_show = by_m_show.rename(columns={"anio_mes_norm": "anio_mes"})
                        st.dataframe(by_m_show, use_container_width=True, height=220)


# -----------------------------
# TAB SUBRUBRO (Punto 3)
# -----------------------------
with tab_subrubro:
    st.subheader("Análisis por subrubro")

    subrubro_sel = st.selectbox("Elegí un subrubro", options=sorted(df["subrubro"].unique().tolist()))
    topk_sr = st.slider("Top sugerencias", min_value=3, max_value=30, value=10, step=1)

    rec_sr = recommend_for_subrubro(subrubro_sel, co, freq, topk=topk_sr)
    rec_sr_show = rec_sr.copy()
    rec_sr_show["score_cooc"] = rec_sr_show["score_cooc"].fillna(0).astype(int)
    rec_sr_show["freq_global"] = rec_sr_show["freq_global"].fillna(0).astype(int)

    st.markdown("### 🔗 Subrubros que suelen comprarse junto con este")
    st.dataframe(rec_sr_show.rename(columns={"score_cooc": "score_similitud"}), use_container_width=True, height=320)

    st.markdown("### 👥 Clientes con mayor compra en este subrubro (por importe)")
    top_clients = (
        df[df["subrubro"] == subrubro_sel]
        .groupby("cliente", as_index=False)
        .agg(importe=("importe", "sum"), unidades=("unidades", "sum"), pedidos=("cant_pedidos", "sum"))
        .sort_values("importe", ascending=False)
        .head(25)
    )
    top_clients_show = top_clients.copy()
    top_clients_show["importe"] = top_clients_show["importe"].map(fmt_money)
    top_clients_show["unidades"] = top_clients_show["unidades"].round(0).astype(int)
    top_clients_show["pedidos"] = top_clients_show["pedidos"].round(0).astype(int)
    st.dataframe(top_clients_show, use_container_width=True, height=360)
