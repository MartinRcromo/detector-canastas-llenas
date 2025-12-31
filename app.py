# app.py — Detector de Canastas Llenas (Puntos 1–4 PRO)
# Streamlit Cloud: main file = app.py
# requirements.txt: streamlit, pandas, numpy

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
    name = (uploaded_file.name or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
        return _normalize_columns(df)

    raw = uploaded_file.getvalue()
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
    "anio_mes": ["anio_mes", "año_mes", "periodo", "mes", "year_month"],
    "articulo_codigo": ["articulo_codigo", "articulo_cod", "codigo_articulo", "sku", "articulo"],
    "articulo_descripcion": ["articulo_descripcion", "descripcion", "articulo_desc", "producto"],
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

    if "articulo_codigo" not in mapping or "articulo_descripcion" not in mapping:
        raise ValueError("Para el Punto 4 necesito articulo_codigo y articulo_descripcion.")

    df = df.rename(columns={v: k for k, v in mapping.items()})

    if "cliente" not in df.columns and "cliente_id" in df.columns:
        df["cliente"] = df["cliente_id"].astype(str)

    df["cliente"] = df["cliente"].astype(str).str.strip()
    df["subrubro"] = df["subrubro"].astype(str).str.strip()
    df["articulo_codigo"] = df["articulo_codigo"].astype(str).str.strip()
    df["articulo_descripcion"] = df["articulo_descripcion"].astype(str).str.strip()

    df["importe"] = _to_number(df.get("importe", pd.Series([0] * len(df)))).fillna(0.0)
    df["unidades"] = _to_number(df.get("unidades", pd.Series([0] * len(df)))).fillna(0.0)
    df["cant_pedidos"] = _to_number(df.get("cant_pedidos", pd.Series([1] * len(df)))).fillna(1.0)

    if "anio_mes" in df.columns:
        df["anio_mes"] = df["anio_mes"].astype(str).str.strip()

    df = df[
        df["cliente"].ne("")
        & df["subrubro"].ne("")
        & df["articulo_codigo"].ne("")
        & df["articulo_descripcion"].ne("")
    ]
    return df


def fmt_int(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def fmt_money(n: float) -> str:
    return f"{float(n):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def metric_col_name(rank_metric: str) -> str:
    return {"importe": "importe", "unidades": "unidades", "pedidos": "cant_pedidos"}[rank_metric]


def normalize_period(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("/", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if m:
        y, mo = m.group(1), int(m.group(2))
        return f"{y}{mo:02d}"
    m2 = re.match(r"^(\d{6})$", s)
    if m2:
        return s
    digs = re.sub(r"\D", "", s)
    if len(digs) == 6:
        return digs
    return s


# -----------------------------
# Modelo (cache)
# -----------------------------
@st.cache_data(show_spinner=False)
def build_model(df: pd.DataFrame):
    agg_cs = df.groupby(["cliente", "subrubro"], as_index=False).agg(
        cant_pedidos=("cant_pedidos", "sum"),
        unidades=("unidades", "sum"),
        importe=("importe", "sum"),
    )

    pivot_pedidos = agg_cs.pivot_table(
        index="cliente",
        columns="subrubro",
        values="cant_pedidos",
        aggfunc="sum",
        fill_value=0.0,
    )

    # binaria + normas para cosine similarity (clientes similares)
    X_bin = (pivot_pedidos > 0).astype(np.float32).values
    norms = np.linalg.norm(X_bin, axis=1)
    norms[norms == 0] = 1.0

    clients = pivot_pedidos.index.to_numpy()
    subrubros = pivot_pedidos.columns.to_numpy()

    # co-ocurrencia subrubro-subrubro
    co = pd.DataFrame(X_bin.T @ X_bin, index=subrubros, columns=subrubros)

    freq = pivot_pedidos.sum(axis=0).sort_values(ascending=False)

    has_period = "anio_mes" in df.columns
    if has_period:
        df = df.copy()
        df["anio_mes_norm"] = df["anio_mes"].map(normalize_period)

    return df, agg_cs, pivot_pedidos, co, freq, X_bin, norms, clients, subrubros, has_period


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


def top_products_global(df: pd.DataFrame, subrubro: str, rank_metric: str, topn: int, has_period: bool):
    metric_col = metric_col_name(rank_metric)
    dfx = df[df["subrubro"] == subrubro].copy()

    g = (
        dfx.groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)
        .agg(
            importe=("importe", "sum"),
            unidades=("unidades", "sum"),
            pedidos=("cant_pedidos", "sum"),
        )
        .sort_values(metric_col, ascending=False)
        .head(topn)
    )

    if has_period and "anio_mes_norm" in dfx.columns:
        last = (
            dfx.groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)["anio_mes_norm"]
            .max()
            .rename(columns={"anio_mes_norm": "ultimo_mes"})
        )
        g = g.merge(last, on=["articulo_codigo", "articulo_descripcion"], how="left")

    return g


def top_products_similar_clients(
    df: pd.DataFrame,
    selected_cliente: str,
    subrubro: str,
    rank_metric: str,
    topn: int,
    pivot: pd.DataFrame,
    X_bin: np.ndarray,
    norms: np.ndarray,
    clients: np.ndarray,
    has_period: bool,
    neighbors_n: int = 50,
    exclude_already_bought: bool = True,
):
    # si el cliente no está, fallback a global
    if selected_cliente not in pivot.index:
        return top_products_global(df, subrubro, rank_metric, topn, has_period)

    idx = np.where(clients == selected_cliente)[0][0]
    v = X_bin[idx]
    sim = (X_bin @ v) / (norms * norms[idx])
    sim[idx] = -1.0  # excluir a sí mismo

    # top vecinos
    top_idx = np.argsort(sim)[::-1][:neighbors_n]
    neigh_clients = clients[top_idx]
    neigh_sim = sim[top_idx]

    dfx = df[(df["subrubro"] == subrubro) & (df["cliente"].isin(neigh_clients))].copy()

    # ponderar por similitud (opcional): peso = sim del vecino
    weights = pd.DataFrame({"cliente": neigh_clients, "w": neigh_sim})
    dfx = dfx.merge(weights, on="cliente", how="left")
    dfx["w"] = dfx["w"].fillna(0.0)

    # score ponderado por similitud
    # para importe: sum(importe*w), etc.
    metric_col = metric_col_name(rank_metric)
    dfx["importe_w"] = dfx["importe"] * dfx["w"]
    dfx["unidades_w"] = dfx["unidades"] * dfx["w"]
    dfx["pedidos_w"] = dfx["cant_pedidos"] * dfx["w"]

    g = (
        dfx.groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)
        .agg(
            score=("{}{}".format(rank_metric, "_w") if rank_metric != "pedidos" else "pedidos_w", "sum"),
            importe=("importe", "sum"),
            unidades=("unidades", "sum"),
            pedidos=("cant_pedidos", "sum"),
            vecinos=("cliente", "nunique"),
        )
        .sort_values("score", ascending=False)
    )

    # excluir productos ya comprados por el cliente (en ese subrubro)
    if exclude_already_bought:
        bought = set(
            df[(df["cliente"] == selected_cliente) & (df["subrubro"] == subrubro)]["articulo_codigo"].unique().tolist()
        )
        g = g[~g["articulo_codigo"].isin(bought)]

    g = g.head(topn)

    if has_period and "anio_mes_norm" in df.columns:
        # ultimo mes global (no por vecino)
        last = (
            df[df["subrubro"] == subrubro]
            .groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)["anio_mes_norm"]
            .max()
            .rename(columns={"anio_mes_norm": "ultimo_mes"})
        )
        g = g.merge(last, on=["articulo_codigo", "articulo_descripcion"], how="left")

    return g


# -----------------------------
# UI
# -----------------------------
st.title(TITLE)
st.caption(SUBTITLE)

with st.sidebar:
    st.header("Datos")
    uploaded = st.file_uploader("Subí tu archivo (CSV/Excel)", type=["csv", "xlsx", "xls"])
    st.divider()
    st.caption("Tip: si el CSV viene de Excel, suele venir con ';' como separador (este loader lo detecta).")

if uploaded is None:
    st.info("Subí un archivo para empezar.")
    st.stop()

try:
    df_raw = read_any_table(uploaded)
except Exception as e:
    st.error(str(e))
    st.stop()

try:
    df_std = standardize(df_raw)
except Exception as e:
    st.error(f"No pude interpretar columnas: {e}")
    st.write("Columnas detectadas:", list(df_raw.columns))
    st.stop()

with st.spinner("Armando modelo..."):
    df, agg_cs, pivot, co, freq, X_bin, norms, clients, subrubros, has_period = build_model(df_std)

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Filas", fmt_int(len(df)))
c2.metric("Clientes", fmt_int(df["cliente"].nunique()))
c3.metric("Subrubros", fmt_int(df["subrubro"].nunique()))

st.divider()

tab_cliente, tab_subrubro = st.tabs(["🔎 Por cliente (Punto 1 + 2 + 4 PRO)", "🧭 Por subrubro (Punto 3)"])


# -----------------------------
# TAB CLIENTE
# -----------------------------
with tab_cliente:
    st.subheader("Buscar cliente")

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
        if str(r.get("cliente_id", "")).strip() and str(r.get("cliente_id", "")).lower() != "nan":
            parts.append(f"ID {str(r['cliente_id']).strip()}")
        if str(r.get("cuit", "")).strip() and str(r.get("cuit", "")).lower() != "nan":
            parts.append(f"CUIT {str(r['cuit']).strip()}")
        return " | ".join(parts)

    base["label"] = base.apply(make_label, axis=1)

    q = st.text_input(
        "Buscar por Razón Social / Código Cliente / CUIT",
        value="",
        placeholder="Ej: fridman, 167, 20-211...",
    )
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

    selected_cliente = selected_label.split("|")[0].strip()

    left, right = st.columns([1.1, 0.9], gap="large")

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

        sub_show = sub.copy()
        sub_show["importe"] = sub_show["importe"].map(fmt_money)
        sub_show["unidades"] = sub_show["unidades"].round(0).astype(int)
        sub_show["cant_pedidos"] = sub_show["cant_pedidos"].round(0).astype(int)
        sub_show = sub_show.rename(columns={"cant_pedidos": "pedidos"})
        st.dataframe(sub_show, use_container_width=True, height=420)

    with right:
        st.markdown("### 💡 Sugerencias de Venta Cruzada (Top 10) + Productos (Punto 2)")
        rank_metric = st.radio(
            "¿Cómo querés rankear?",
            ["importe", "unidades", "pedidos"],
            index=0,
            horizontal=True,
        )
        top_subrubros = st.slider("Cantidad de subrubros oportunidad", min_value=3, max_value=25, value=10, step=1)

        rec = recommend_for_client(selected_cliente, pivot, co, freq, topk=top_subrubros)
        rec_show = rec.copy()
        rec_show["score_cooc"] = rec_show["score_cooc"].fillna(0).astype(int)
        rec_show["freq_global"] = rec_show["freq_global"].fillna(0).astype(int)
        st.dataframe(rec_show.rename(columns={"score_cooc": "score_similitud"}), use_container_width=True, height=260)

        st.markdown("### 🧠 Plan de acción (Punto 4 PRO)")

        source_mode = st.radio(
            "Fuente de productos sugeridos",
            ["Clientes similares (recomendado)", "Global (más vendidos)"],
            index=0,
            horizontal=False,
        )

        top_products = st.slider("Productos por subrubro", min_value=3, max_value=30, value=10, step=1)

        neighbors_n = st.slider("Cantidad de clientes similares a mirar", min_value=10, max_value=200, value=50, step=10)
        exclude_bought = st.checkbox("Excluir productos que el cliente ya compra en ese subrubro", value=True)

        st.caption(
            "Tip: “Clientes similares” suele dar mejores sugerencias porque replica canastas reales parecidas al cliente objetivo."
        )

        for _, row in rec.head(top_subrubros).iterrows():
            sr = row["subrubro"]
            score = int(row["score_cooc"]) if pd.notna(row["score_cooc"]) else 0

            with st.expander(f"📌 {sr} — score {score}", expanded=False):
                if source_mode.startswith("Clientes similares"):
                    g = top_products_similar_clients(
                        df=df,
                        selected_cliente=selected_cliente,
                        subrubro=sr,
                        rank_metric=rank_metric,
                        topn=top_products,
                        pivot=pivot,
                        X_bin=X_bin,
                        norms=norms,
                        clients=clients,
                        has_period=has_period,
                        neighbors_n=neighbors_n,
                        exclude_already_bought=exclude_bought,
                    )

                    # formateo
                    show = g.copy()
                    if "importe" in show.columns:
                        show["importe"] = show["importe"].map(fmt_money)
                    show["unidades"] = show["unidades"].round(0).astype(int)
                    show["pedidos"] = show["pedidos"].round(0).astype(int)
                    if "score" in show.columns:
                        show["score"] = show["score"].round(2)

                    cols = ["articulo_codigo", "articulo_descripcion", "score", "vecinos", "importe", "unidades", "pedidos"]
                    if has_period and "ultimo_mes" in show.columns:
                        cols.append("ultimo_mes")

                    st.dataframe(show[cols], use_container_width=True, height=280)

                else:
                    g = top_products_global(df=df, subrubro=sr, rank_metric=rank_metric, topn=top_products, has_period=has_period)

                    show = g.copy()
                    show["importe"] = show["importe"].map(fmt_money)
                    show["unidades"] = show["unidades"].round(0).astype(int)
                    show["pedidos"] = show["pedidos"].round(0).astype(int)

                    cols = ["articulo_codigo", "articulo_descripcion", "importe", "unidades", "pedidos"]
                    if has_period and "ultimo_mes" in show.columns:
                        cols.append("ultimo_mes")

                    st.dataframe(show[cols], use_container_width=True, height=280)

                # mini tendencia mensual del subrubro (si hay periodo)
                if has_period and "anio_mes_norm" in df.columns:
                    dfx_sr = df[df["subrubro"] == sr].copy()
                    by_m = (
                        dfx_sr.groupby("anio_mes_norm", as_index=False)
                        .agg(importe=("importe", "sum"), unidades=("unidades", "sum"), pedidos=("cant_pedidos", "sum"))
                        .sort_values("anio_mes_norm", ascending=True)
                        .tail(12)
                    )
                    by_m_show = by_m.copy()
                    by_m_show["importe"] = by_m_show["importe"].map(fmt_money)
                    by_m_show["unidades"] = by_m_show["unidades"].round(0).astype(int)
                    by_m_show["pedidos"] = by_m_show["pedidos"].round(0).astype(int)
                    by_m_show = by_m_show.rename(columns={"anio_mes_norm": "anio_mes"})
                    st.caption("📈 Tendencia mensual del subrubro (últimos 12 meses)")
                    st.dataframe(by_m_show, use_container_width=True, height=210)


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
