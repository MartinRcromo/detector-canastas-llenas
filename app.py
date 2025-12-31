# app.py — Detector de Canastas Llenas (Multi-empresa + Unificación por CUIT + Filtro vendedor + SQLite)
# requirements.txt: streamlit, pandas, numpy

import io
import os
import re
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st


# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

TITLE = "🧺 Detector de Canastas Llenas"
SUBTITLE = "Cross-selling por co-ocurrencia de subrubros. Unificación cliente por CUIT (Cromosol + BBA)."

DB_PATH = "data_cache.sqlite"


# -----------------------------
# UI - Header
# -----------------------------
st.title(TITLE)
st.caption(SUBTITLE)


# -----------------------------
# Helpers: columnas / números / lectura
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

    # Heurística: si contiene coma -> decimal coma y miles punto
    mask_comma = s.str.contains(",", regex=False)
    s.loc[mask_comma] = (
        s.loc[mask_comma]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    s.loc[~mask_comma] = s.loc[~mask_comma].str.replace(",", "", regex=False)

    s = s.str.replace(r"[^\d\.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def _guess_sep_and_read(raw: bytes) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "latin1", "utf-16"]
    seps = [";", ",", "\t", "|"]

    last_err = None
    for enc in encodings:
        for sep in seps:
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=sep, encoding=enc)
                if df.shape[1] <= 1:
                    continue
                return df
            except Exception as e:
                last_err = e
                continue
    raise RuntimeError(f"No pude leer el archivo. Último error: {last_err}")


def read_any_table(uploaded_file) -> pd.DataFrame:
    name = (uploaded_file.name or "").lower()

    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
        return _normalize_columns(df)

    raw = uploaded_file.getvalue()
    df = _guess_sep_and_read(raw)
    return _normalize_columns(df)


def infer_empresa_from_filename(filename: str) -> str:
    fn = (filename or "").lower()
    if "cromo" in fn:
        return "CROMOSOL"
    if "bba" in fn:
        return "BBA"
    # fallback
    return "SIN_ETIQUETA"


# -----------------------------
# Mapeo de columnas esperadas
# -----------------------------
REQUIRED = {
    "cliente": ["cliente", "razonsocial", "razon_social", "razon", "cliente_nombre"],
    "cliente_id": ["cliente_id", "cliente_codigo", "codigo_cliente", "id_cliente", "nro_cliente", "numero_cliente"],
    "cuit": ["cuit", "cuit_cliente", "tax_id", "cuitcuil", "cuil"],
    "subrubro": ["subrubro", "articulo_sub_rubro", "articulo_subrubro", "sub_rubro", "subrubros"],
    "importe": ["importe", "monto", "total", "neto", "importe_neto"],
    "unidades": ["unidades", "unidad", "qty", "cantidad"],
    "cant_pedidos": ["cant_pedidos", "cantidad_pedidos", "cant_pedido", "pedidos", "cantidad_pedidos_distintos"],
    "anio_mes": ["anio_mes", "año_mes", "periodo", "mes", "year_month", "anio_mes_norm"],
    "articulo_codigo": ["articulo_codigo", "articulo_cod", "codigo_articulo", "sku", "articulo", "codigo"],
    "articulo_descripcion": ["articulo_descripcion", "descripcion", "articulo_desc", "producto", "desc"],
    # NUEVO: vendedor
    "vendedor": ["vendedor", "cod_vendedor", "vendedor_id", "vendedor_nombre", "sales_rep", "representante"],
}


def pick_col(df_cols, candidates):
    for c in candidates:
        if c in df_cols:
            return c
    return None


def clean_cuit(x) -> str:
    s = str(x or "").strip()
    s = re.sub(r"\D", "", s)
    # CUIT típico 11 dígitos. Si viene con basura igual lo dejamos numérico.
    return s


def standardize_one(df: pd.DataFrame, empresa: str) -> pd.DataFrame:
    df = df.copy()
    cols = set(df.columns)

    mapping = {}
    for std_name, candidates in REQUIRED.items():
        col = pick_col(cols, candidates)
        if col:
            mapping[std_name] = col

    if "subrubro" not in mapping:
        raise ValueError("Falta columna de subrubro (ej: 'subrubro').")

    if "cliente" not in mapping and "cliente_id" not in mapping:
        raise ValueError("Falta columna de cliente (razón social o id).")

    if "articulo_codigo" not in mapping or "articulo_descripcion" not in mapping:
        raise ValueError("Necesito articulo_codigo y articulo_descripcion para productos (Punto 4).")

    df = df.rename(columns={v: k for k, v in mapping.items()})

    # defaults
    if "cliente" not in df.columns and "cliente_id" in df.columns:
        df["cliente"] = df["cliente_id"].astype(str)

    if "cliente_id" not in df.columns:
        df["cliente_id"] = ""

    if "cuit" not in df.columns:
        df["cuit"] = ""

    if "vendedor" not in df.columns:
        df["vendedor"] = ""

    df["empresa"] = empresa

    # clean
    df["cliente"] = df["cliente"].astype(str).str.strip()
    df["cliente_id"] = df["cliente_id"].astype(str).str.strip()
    df["cuit"] = df["cuit"].map(clean_cuit)
    df["vendedor"] = df["vendedor"].astype(str).str.strip()

    df["subrubro"] = df["subrubro"].astype(str).str.strip()
    df["articulo_codigo"] = df["articulo_codigo"].astype(str).str.strip()
    df["articulo_descripcion"] = df["articulo_descripcion"].astype(str).str.strip()

    df["importe"] = _to_number(df.get("importe", pd.Series([0] * len(df)))).fillna(0.0)
    df["unidades"] = _to_number(df.get("unidades", pd.Series([0] * len(df)))).fillna(0.0)

    # si no viene cant_pedidos, ponemos 1 por fila (aprox)
    if "cant_pedidos" in df.columns:
        df["cant_pedidos"] = _to_number(df["cant_pedidos"]).fillna(0.0)
        df.loc[df["cant_pedidos"] <= 0, "cant_pedidos"] = 1.0
    else:
        df["cant_pedidos"] = 1.0

    if "anio_mes" in df.columns:
        df["anio_mes"] = df["anio_mes"].astype(str).str.strip()
    else:
        df["anio_mes"] = ""

    # filtro de filas mínimas
    df = df[
        df["cliente"].ne("")
        & df["subrubro"].ne("")
        & df["articulo_codigo"].ne("")
        & df["articulo_descripcion"].ne("")
    ].copy()

    # clave unificada por CUIT (si falta CUIT, fallback por cliente normalizado)
    # OJO: para unificar por CUIT sí o sí, ideal que venga CUIT.
    df["cliente_key"] = df["cuit"]
    df.loc[df["cliente_key"].eq("") | df["cliente_key"].isna(), "cliente_key"] = (
        df["cliente"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip().map(lambda x: f"NO_CUIT::{x}")
    )

    return df


def fmt_int(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")


def fmt_money(n: float) -> str:
    return f"{float(n):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def metric_col_name(rank_metric: str) -> str:
    return {"importe": "importe", "unidades": "unidades", "pedidos": "cant_pedidos"}[rank_metric]


def normalize_period(s: str) -> str:
    s = (s or "").strip().replace("/", "-")
    m = re.match(r"^(\d{4})-(\d{1,2})$", s)
    if m:
        y, mo = m.group(1), int(m.group(2))
        return f"{y}{mo:02d}"
    digs = re.sub(r"\D", "", s)
    if len(digs) == 6:
        return digs
    return s


# -----------------------------
# SQLite: guardar / cargar
# -----------------------------
def db_init():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ventas (
            empresa TEXT,
            cliente_key TEXT,
            cuit TEXT,
            cliente TEXT,
            cliente_id TEXT,
            vendedor TEXT,
            subrubro TEXT,
            importe REAL,
            unidades REAL,
            cant_pedidos REAL,
            anio_mes TEXT,
            articulo_codigo TEXT,
            articulo_descripcion TEXT,
            loaded_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def db_clear():
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM ventas")
    conn.commit()
    conn.close()


def db_save_df(df: pd.DataFrame):
    db_init()
    conn = sqlite3.connect(DB_PATH)
    out = df.copy()
    out["loaded_at"] = datetime.now().isoformat(timespec="seconds")
    out.to_sql("ventas", conn, if_exists="append", index=False)
    conn.close()


def db_load_df() -> pd.DataFrame:
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ventas", conn)
    conn.close()
    return df


# -----------------------------
# Modelo (cache)
# -----------------------------
@st.cache_data(show_spinner=False)
def build_model(df: pd.DataFrame):
    df = df.copy()
    df["anio_mes_norm"] = df["anio_mes"].map(normalize_period)

    # agregación cliente_key x subrubro (UNIFICADO)
    agg_cs = df.groupby(["cliente_key", "subrubro"], as_index=False).agg(
        cant_pedidos=("cant_pedidos", "sum"),
        unidades=("unidades", "sum"),
        importe=("importe", "sum"),
    )

    pivot_pedidos = agg_cs.pivot_table(
        index="cliente_key",
        columns="subrubro",
        values="cant_pedidos",
        aggfunc="sum",
        fill_value=0.0,
    )

    X_bin = (pivot_pedidos > 0).astype(np.float32).values
    norms = np.linalg.norm(X_bin, axis=1)
    norms[norms == 0] = 1.0

    clients = pivot_pedidos.index.to_numpy()
    subrubros = pivot_pedidos.columns.to_numpy()

    co = pd.DataFrame(X_bin.T @ X_bin, index=subrubros, columns=subrubros)
    freq = pivot_pedidos.sum(axis=0).sort_values(ascending=False)

    return df, agg_cs, pivot_pedidos, co, freq, X_bin, norms, clients, subrubros


def recommend_for_client(cliente_key: str, pivot: pd.DataFrame, co: pd.DataFrame, freq: pd.Series, topk=10):
    if cliente_key not in pivot.index:
        return pd.DataFrame(columns=["subrubro", "score_cooc", "freq_global"])

    owned = pivot.loc[cliente_key]
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


def top_products_similar_clients(
    df: pd.DataFrame,
    selected_cliente_key: str,
    subrubro: str,
    rank_metric: str,
    topn: int,
    pivot: pd.DataFrame,
    X_bin: np.ndarray,
    norms: np.ndarray,
    clients: np.ndarray,
    neighbors_n: int = 50,
    exclude_already_bought: bool = True,
):
    if selected_cliente_key not in pivot.index:
        return pd.DataFrame()

    idx = np.where(clients == selected_cliente_key)[0][0]
    v = X_bin[idx]
    sim = (X_bin @ v) / (norms * norms[idx])
    sim[idx] = -1.0

    top_idx = np.argsort(sim)[::-1][:neighbors_n]
    neigh_clients = clients[top_idx]
    neigh_sim = sim[top_idx]

    dfx = df[(df["subrubro"] == subrubro) & (df["cliente_key"].isin(neigh_clients))].copy()

    weights = pd.DataFrame({"cliente_key": neigh_clients, "w": neigh_sim})
    dfx = dfx.merge(weights, on="cliente_key", how="left")
    dfx["w"] = dfx["w"].fillna(0.0)

    dfx["importe_w"] = dfx["importe"] * dfx["w"]
    dfx["unidades_w"] = dfx["unidades"] * dfx["w"]
    dfx["pedidos_w"] = dfx["cant_pedidos"] * dfx["w"]

    metric_w = {"importe": "importe_w", "unidades": "unidades_w", "pedidos": "pedidos_w"}[rank_metric]

    g = (
        dfx.groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)
        .agg(
            score=(metric_w, "sum"),
            importe=("importe", "sum"),
            unidades=("unidades", "sum"),
            pedidos=("cant_pedidos", "sum"),
            vecinos=("cliente_key", "nunique"),
            ultimo_mes=("anio_mes_norm", "max"),
        )
        .sort_values("score", ascending=False)
    )

    if exclude_already_bought:
        bought = set(
            df[(df["cliente_key"] == selected_cliente_key) & (df["subrubro"] == subrubro)]["articulo_codigo"].unique()
        )
        g = g[~g["articulo_codigo"].isin(bought)]

    return g.head(topn)


# -----------------------------
# Sidebar - Fuentes de datos
# -----------------------------
with st.sidebar:
    st.header("Datos")
    mode = st.radio("Fuente", ["Subir archivos", "Usar base (SQLite)"], index=0)

    if mode == "Subir archivos":
        uploads = st.file_uploader(
            "Subí 1 o 2 archivos (CSV/Excel) — Cromosol y/o BBA",
            type=["csv", "xlsx", "xls"],
            accept_multiple_files=True,
        )
        st.caption("Tip: si el nombre del archivo contiene 'bba' o 'cromo' lo etiqueta solo como empresa.")

        colA, colB = st.columns(2)
        with colA:
            save_to_db = st.checkbox("Guardar en base (SQLite)", value=True)
        with colB:
            if st.button("🧽 Limpiar base", use_container_width=True):
                db_clear()
                st.success("Base limpiada.")

    else:
        st.info("Cargando datos desde la base SQLite local…")
        colA, colB = st.columns(2)
        with colA:
            if st.button("🔄 Recargar base", use_container_width=True):
                st.cache_data.clear()
        with colB:
            if st.button("🧽 Limpiar base", use_container_width=True):
                db_clear()
                st.success("Base limpiada.")


# -----------------------------
# Carga de datos
# -----------------------------
df_all = None

if mode == "Usar base (SQLite)":
    df_db = db_load_df()
    if df_db.empty:
        st.warning("La base está vacía. Elegí 'Subir archivos' y guardá en base.")
        st.stop()
    df_all = df_db.copy()

else:
    if not uploads:
        st.info("Subí al menos un archivo para empezar.")
        st.stop()

    frames = []
    for up in uploads:
        try:
            df_raw = read_any_table(up)
            empresa = infer_empresa_from_filename(up.name)
            df_std = standardize_one(df_raw, empresa=empresa)
            frames.append(df_std)
        except Exception as e:
            st.error(f"Error leyendo {up.name}: {e}")
            st.stop()

    df_all = pd.concat(frames, ignore_index=True)

    if save_to_db:
        # estrategia simple: limpiar y guardar todo (para evitar duplicados)
        # después lo refinamos con "dataset_id" si querés histórico.
        db_clear()
        db_save_df(df_all)
        st.success("Guardado en base (SQLite).")


# -----------------------------
# Filtro por vendedor (si existe)
# -----------------------------
has_vendedor = df_all["vendedor"].astype(str).str.strip().ne("").any()
if has_vendedor:
    vendedores = sorted([v for v in df_all["vendedor"].dropna().astype(str).unique().tolist() if v.strip() != ""])
    with st.sidebar:
        st.divider()
        st.header("Filtro")
        vendedor_sel = st.selectbox("Vendedor", options=["(Todos)"] + vendedores, index=0)
    if vendedor_sel != "(Todos)":
        df_all = df_all[df_all["vendedor"] == vendedor_sel].copy()
else:
    with st.sidebar:
        st.divider()
        st.caption("⚠️ No detecté columna de vendedor (o viene vacía). El filtro de vendedor no se aplicará.")


# -----------------------------
# KPIs + Info unificación
# -----------------------------
# “Clientes” = cliente_key unificado
c1, c2, c3, c4 = st.columns(4)
c1.metric("Filas", fmt_int(len(df_all)))
c2.metric("Clientes unificados", fmt_int(df_all["cliente_key"].nunique()))
c3.metric("Subrubros", fmt_int(df_all["subrubro"].nunique()))
c4.metric("Empresas", fmt_int(df_all["empresa"].nunique()))

st.divider()


# -----------------------------
# Construir modelo
# -----------------------------
with st.spinner("Armando modelo…"):
    df, agg_cs, pivot, co, freq, X_bin, norms, clients, subrubros = build_model(df_all)


# -----------------------------
# Catálogo de clientes unificados (para buscador)
# -----------------------------
def build_customer_catalog(df: pd.DataFrame) -> pd.DataFrame:
    # Para cada cliente_key armamos un resumen:
    # - CUIT
    # - razones sociales (pueden ser diferentes)
    # - IDs por empresa
    base = df.groupby("cliente_key", as_index=False).agg(
        cuit=("cuit", lambda s: next((x for x in s.astype(str).tolist() if x.strip() != ""), "")),
        empresas=("empresa", lambda s: sorted(list(set([x for x in s.astype(str).tolist() if x])))),
        razones=("cliente", lambda s: sorted(list(set([x for x in s.astype(str).tolist() if x.strip() != ""])))),
        ids=("cliente_id", lambda s: sorted(list(set([x for x in s.astype(str).tolist() if x.strip() != ""])))),
    )

    # IDs por empresa (si querés verlo explícito)
    # armamos string “CROMOSOL:123 | BBA:987”
    pairs = (
        df[["cliente_key", "empresa", "cliente_id"]]
        .drop_duplicates()
        .assign(cliente_id=lambda x: x["cliente_id"].astype(str).str.strip())
    )
    pairs = pairs[pairs["cliente_id"].ne("")].copy()
    by_key = pairs.groupby("cliente_key").apply(
        lambda g: " | ".join([f"{r['empresa']}:{r['cliente_id']}" for _, r in g.iterrows()])
    )
    base["ids_por_empresa"] = base["cliente_key"].map(by_key).fillna("")

    def label(r):
        cuit = r["cuit"] if r["cuit"] else "SIN_CUIT"
        name = r["razones"][0] if r["razones"] else "(sin nombre)"
        extra = ""
        if r["ids_por_empresa"]:
            extra = f" | {r['ids_por_empresa']}"
        # si hay más de 1 razón, lo indicamos
        if len(r["razones"]) > 1:
            extra += f" | +{len(r['razones'])-1} razones"
        return f"{name} | CUIT {cuit}{extra}"

    base["label"] = base.apply(label, axis=1)
    return base


catalog = build_customer_catalog(df)


# -----------------------------
# Tabs
# -----------------------------
tab_cliente, tab_subrubro = st.tabs(["🔎 Por cliente (1+2+4)", "🧭 Por subrubro (3)"])


# -----------------------------
# TAB CLIENTE
# -----------------------------
with tab_cliente:
    st.subheader("Buscar cliente (unificado por CUIT)")
    q = st.text_input("Buscar por Razón Social / ID / CUIT", value="", placeholder="Ej: fridman, 167, 202111...")
    q_norm = q.strip().lower()

    if q_norm:
        mask = catalog["label"].str.lower().str.contains(re.escape(q_norm), na=False)
        options = catalog.loc[mask, "label"].tolist()
        if not options:
            st.warning("No encontré clientes con ese texto. Probá otra parte del nombre, un ID, o el CUIT.")
            st.stop()
    else:
        options = catalog["label"].tolist()

    selected_label = st.selectbox("Seleccioná un cliente", options=options, index=0 if options else None)
    if not selected_label:
        st.stop()

    selected_key = catalog.loc[catalog["label"] == selected_label, "cliente_key"].iloc[0]
    selected_row = catalog[catalog["cliente_key"] == selected_key].iloc[0]

    # Mostrar info unificada
    with st.expander("📌 Cliente unificado detectado (detalle)", expanded=True):
        st.write(f"**CUIT:** {selected_row['cuit'] or 'SIN_CUIT'}")
        st.write(f"**Empresas:** {', '.join(selected_row['empresas']) if selected_row['empresas'] else '-'}")
        st.write(f"**IDs por empresa:** {selected_row['ids_por_empresa'] or '-'}")
        if selected_row["razones"]:
            st.write("**Razones sociales detectadas:**")
            for rs in selected_row["razones"][:10]:
                st.write(f"- {rs}")
            if len(selected_row["razones"]) > 10:
                st.caption(f"(+ {len(selected_row['razones'])-10} más)")

    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.markdown("### 📦 Subrubros que compra (unificado)")
        sub = (
            agg_cs[agg_cs["cliente_key"] == selected_key]
            .groupby("subrubro", as_index=False)
            .agg(
                pedidos=("cant_pedidos", "sum"),
                unidades=("unidades", "sum"),
                importe=("importe", "sum"),
            )
            .sort_values("importe", ascending=False)
        )
        show = sub.copy()
        show["importe"] = show["importe"].map(fmt_money)
        show["unidades"] = show["unidades"].round(0).astype(int)
        show["pedidos"] = show["pedidos"].round(0).astype(int)
        st.dataframe(show, use_container_width=True, height=420)

    with right:
        st.markdown("### 💡 Sugerencias de venta cruzada + productos")
        rank_metric = st.radio("Rankear por", ["importe", "unidades", "pedidos"], index=0, horizontal=True)
        top_subrubros = st.slider("Cantidad de subrubros oportunidad", 3, 25, 10, 1)
        top_products = st.slider("Productos por subrubro", 3, 30, 10, 1)
        neighbors_n = st.slider("Clientes similares a mirar", 10, 200, 50, 10)
        exclude_bought = st.checkbox("Excluir productos que ya compra", value=True)

        rec = recommend_for_client(selected_key, pivot, co, freq, topk=top_subrubros)
        rec_show = rec.copy()
        rec_show["score_cooc"] = rec_show["score_cooc"].fillna(0).astype(int)
        rec_show["freq_global"] = rec_show["freq_global"].fillna(0).astype(int)
        st.dataframe(rec_show.rename(columns={"score_cooc": "score_similitud"}), use_container_width=True, height=260)

        st.markdown("### 🧠 Plan de acción (clientes similares)")
        for _, row in rec.head(top_subrubros).iterrows():
            sr = row["subrubro"]
            score = int(row["score_cooc"]) if pd.notna(row["score_cooc"]) else 0

            with st.expander(f"📌 {sr} — score {score}", expanded=False):
                g = top_products_similar_clients(
                    df=df,
                    selected_cliente_key=selected_key,
                    subrubro=sr,
                    rank_metric=rank_metric,
                    topn=top_products,
                    pivot=pivot,
                    X_bin=X_bin,
                    norms=norms,
                    clients=clients,
                    neighbors_n=neighbors_n,
                    exclude_already_bought=exclude_bought,
                )

                if g.empty:
                    st.info("Sin datos suficientes para armar ranking por clientes similares.")
                else:
                    showp = g.copy()
                    showp["importe"] = showp["importe"].map(fmt_money)
                    showp["unidades"] = showp["unidades"].round(0).astype(int)
                    showp["pedidos"] = showp["pedidos"].round(0).astype(int)
                    showp["score"] = showp["score"].round(2)

                    st.dataframe(
                        showp[
                            ["articulo_codigo", "articulo_descripcion", "score", "vecinos", "importe", "unidades", "pedidos", "ultimo_mes"]
                        ],
                        use_container_width=True,
                        height=280,
                    )


# -----------------------------
# TAB SUBRUBRO (Punto 3)
# -----------------------------
with tab_subrubro:
    st.subheader("Análisis por subrubro")
    subrubro_sel = st.selectbox("Elegí un subrubro", options=sorted(df["subrubro"].unique().tolist()))
    topk_sr = st.slider("Top sugerencias", 3, 30, 10, 1)

    # co-ocurrencia por subrubro
    if subrubro_sel not in co.index:
        st.warning("No pude encontrar ese subrubro en la matriz.")
        st.stop()

    scores = co.loc[subrubro_sel].drop(index=subrubro_sel).sort_values(ascending=False).head(topk_sr)
    rec_sr = pd.DataFrame(
        {
            "subrubro": scores.index,
            "score_similitud": scores.values.astype(int),
            "freq_global": freq.reindex(scores.index).fillna(0).astype(int).values,
        }
    )
    st.markdown("### 🔗 Subrubros que suelen comprarse junto con este")
    st.dataframe(rec_sr, use_container_width=True, height=320)

    st.markdown("### 👥 Clientes unificados con mayor compra (por importe)")
    top_clients = (
        df[df["subrubro"] == subrubro_sel]
        .groupby("cliente_key", as_index=False)
        .agg(importe=("importe", "sum"), unidades=("unidades", "sum"), pedidos=("cant_pedidos", "sum"))
        .sort_values("importe", ascending=False)
        .head(25)
    )
    top_clients = top_clients.merge(catalog[["cliente_key", "label"]], on="cliente_key", how="left")
    showc = top_clients.copy()
    showc["importe"] = showc["importe"].map(fmt_money)
    showc["unidades"] = showc["unidades"].round(0).astype(int)
    showc["pedidos"] = showc["pedidos"].round(0).astype(int)
    showc = showc.rename(columns={"label": "cliente_unificado"})
    st.dataframe(showc[["cliente_unificado", "importe", "unidades", "pedidos"]], use_container_width=True, height=360)
