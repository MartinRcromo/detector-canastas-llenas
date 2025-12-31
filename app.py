import io
import re
import unicodedata
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st
from difflib import get_close_matches


# -----------------------------
# Helpers: normalización / fuzzy
# -----------------------------
def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])  # sin acentos
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9_ ]", "", s)
    return s


def _best_col_match(cols, target_keys):
    """
    cols: lista de columnas originales
    target_keys: lista de posibles nombres "canon" (ya normalizados)
    Devuelve la mejor columna original para mapear.
    """
    norm_map = {c: _normalize(c) for c in cols}
    norm_cols = list(norm_map.values())

    for tk in target_keys:
        # match directo
        if tk in norm_cols:
            idx = norm_cols.index(tk)
            return cols[idx]
        # match aproximado
        m = get_close_matches(tk, norm_cols, n=1, cutoff=0.78)
        if m:
            idx = norm_cols.index(m[0])
            return cols[idx]
    return None


def _to_number(series: pd.Series) -> pd.Series:
    """
    Convierte números con separador decimal ',' o '.' y elimina miles.
    """
    s = series.astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False).str.replace(" ", "", regex=False)

    # si contiene coma, asumimos coma decimal => quitamos puntos miles y cambiamos coma por punto
    mask_comma = s.str.contains(",", regex=False)
    s.loc[mask_comma] = (
        s.loc[mask_comma]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    # si no contiene coma, quitamos comas miles
    s.loc[~mask_comma] = s.loc[~mask_comma].str.replace(",", "", regex=False)

    s = s.str.replace(r"[^\d\.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def _sniff_delimiter(sample_text: str) -> str:
    # probamos delimitadores típicos
    candidates = [",", ";", "\t", "|"]
    counts = {d: sample_text.count(d) for d in candidates}
    # elegimos el que más aparece (y al menos >0)
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _read_csv_robust(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()

    # intentamos encodings comunes en AR/Windows
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            text = raw.decode(enc)
            used_enc = enc
            break
        except UnicodeDecodeError:
            continue
    else:
        # último recurso
        text = raw.decode("latin1", errors="replace")
        used_enc = "latin1(errors=replace)"

    # detectar delimitador con un sample
    sample = text[:100_000]
    sep = _sniff_delimiter(sample)

    df = pd.read_csv(io.StringIO(text), sep=sep)
    df.attrs["__encoding__"] = used_enc
    df.attrs["__sep__"] = sep
    return df


def _read_excel(uploaded_file) -> pd.DataFrame:
    return pd.read_excel(uploaded_file)


# ----------------------------------------
# Ingesta: CSV/Excel + mapeo de columnas
# ----------------------------------------
@st.cache_data(show_spinner=False)
def read_any_table(uploaded_file) -> pd.DataFrame:
    name = (uploaded_file.name or "").lower()

    if name.endswith((".xlsx", ".xls")):
        df = _read_excel(uploaded_file)
    else:
        df = _read_csv_robust(uploaded_file)

    # mapeo flexible a nombres canónicos
    cols = list(df.columns)

    mapping = {}

    # Cliente / IDs
    mapping["cliente_id"] = _best_col_match(cols, ["cliente_id", "id_cliente", "clienteid", "codigocliente", "codigo_cliente"])
    mapping["cuit"] = _best_col_match(cols, ["cuit", "cuil", "taxid", "vat"])
    mapping["RazonSocial"] = _best_col_match(cols, ["razonsocial", "razon social", "cliente", "nombrecliente", "customer", "account"])

    # Subrubro / Artículo
    mapping["subrubro"] = _best_col_match(cols, ["subrubro", "sub_rubro", "sub rubro", "articulo sub rubro", "subrub"])
    mapping["articulo_codigo"] = _best_col_match(cols, ["articulo_codigo", "codigoarticulo", "cod_articulo", "sku", "itemcode", "articulo"])
    mapping["articulo_descripcion"] = _best_col_match(cols, ["articulo_descripcion", "descripcion", "desc_articulo", "itemdescription", "articulo descripcion"])

    # Métricas
    mapping["unidades"] = _best_col_match(cols, ["unidades", "cantidad", "qty", "units"])
    mapping["importe"] = _best_col_match(cols, ["importe", "importe_neto", "neto", "total", "amount", "ventas"])
    mapping["cant_pedidos"] = _best_col_match(cols, ["cant_pedidos", "cantidad_pedidos", "pedidos", "orders"])

    # Nos aseguramos de tener al menos cliente + subrubro
    if mapping["subrubro"] is None:
        raise ValueError("No pude encontrar la columna de subrubro. Esperaba algo como: 'subrubro'.")
    if mapping["RazonSocial"] is None and mapping["cliente_id"] is None:
        raise ValueError("No pude encontrar cliente. Esperaba algo como: 'RazonSocial' o 'cliente_id'.")

    # Renombrar las columnas encontradas a los nombres canónicos
    rename = {v: k for k, v in mapping.items() if v is not None}
    df = df.rename(columns=rename)

    # Garantizar columnas base
    if "RazonSocial" not in df.columns:
        df["RazonSocial"] = df["cliente_id"].astype(str)

    if "cliente_id" not in df.columns:
        df["cliente_id"] = pd.Series([""] * len(df))

    if "cuit" not in df.columns:
        df["cuit"] = pd.Series([""] * len(df))

    if "articulo_codigo" not in df.columns:
        df["articulo_codigo"] = pd.Series([""] * len(df))

    if "articulo_descripcion" not in df.columns:
        df["articulo_descripcion"] = pd.Series([""] * len(df))

    if "cant_pedidos" not in df.columns:
        df["cant_pedidos"] = 0

    # Limpieza tipos
    df["RazonSocial"] = df["RazonSocial"].astype(str).str.strip()
    df["cliente_id"] = df["cliente_id"].astype(str).str.strip()
    df["cuit"] = df["cuit"].astype(str).str.strip()
    df["subrubro"] = df["subrubro"].astype(str).str.strip()
    df["articulo_codigo"] = df["articulo_codigo"].astype(str).str.strip()
    df["articulo_descripcion"] = df["articulo_descripcion"].astype(str).str.strip()

    df["importe"] = _to_number(df.get("importe", pd.Series([0] * len(df)))).fillna(0.0)
    df["unidades"] = _to_number(df.get("unidades", pd.Series([0] * len(df)))).fillna(0.0)
    df["cant_pedidos"] = _to_number(df.get("cant_pedidos", pd.Series([0] * len(df)))).fillna(0.0)

    return df


# ----------------------------------------
# Modelo: índices para recomendaciones
# ----------------------------------------
@st.cache_data(show_spinner=False)
def build_indices(df: pd.DataFrame):
    # subrubros comprados por cliente (set)
    client_sub = (
        df.groupby(["cliente_id", "RazonSocial", "cuit"])["subrubro"]
        .apply(lambda x: set(x.dropna().astype(str)))
        .reset_index()
    )

    # índice: subrubro -> lista de clientes (para armar similares)
    sub_to_clients = defaultdict(list)
    for _, row in client_sub.iterrows():
        key = (row["cliente_id"], row["RazonSocial"], row["cuit"])
        for s in row["subrubro"]:
            sub_to_clients[s].append(key)

    # dict: cliente_key -> set subrubros
    client_to_subs = {}
    for _, row in client_sub.iterrows():
        key = (row["cliente_id"], row["RazonSocial"], row["cuit"])
        client_to_subs[key] = row["subrubro"]

    # agregado por cliente-subrubro (para “subrubros que compra”)
    cs_agg = (
        df.groupby(["cliente_id", "RazonSocial", "cuit", "subrubro"], as_index=False)
        .agg(
            importe=("importe", "sum"),
            unidades=("unidades", "sum"),
            pedidos=("cant_pedidos", "sum"),
        )
    )

    return client_to_subs, sub_to_clients, cs_agg


def recommend_subrubros(client_key, client_to_subs, sub_to_clients, top_k=10):
    """
    Recomienda subrubros que el cliente NO compra, ponderados por similitud (overlap de subrubros).
    """
    my_subs = client_to_subs.get(client_key, set())
    if not my_subs:
        return [], set(), {}

    # candidatos: clientes que comparten subrubro con el cliente
    sim_counter = Counter()
    candidate_clients = set()
    for s in my_subs:
        for ck in sub_to_clients.get(s, []):
            if ck == client_key:
                continue
            sim_counter[ck] += 1
            candidate_clients.add(ck)

    if not candidate_clients:
        return [], set(), {}

    # score por subrubro: suma de similitud de clientes que lo compran
    sub_score = Counter()
    for ck, w in sim_counter.items():
        subs_other = client_to_subs.get(ck, set())
        for s in subs_other:
            if s not in my_subs:
                sub_score[s] += w

    # top recomendaciones
    recs = sub_score.most_common(top_k)
    # devolvemos también similitudes para usar en productos
    return recs, candidate_clients, dict(sim_counter)


def top_products_for_subrubro(df: pd.DataFrame, subrubro: str, candidate_clients: set, metric="importe", top_n=8):
    """
    Productos más importantes del subrubro, mirando SOLO clientes similares (candidate_clients).
    """
    if not candidate_clients:
        return pd.DataFrame(columns=["articulo_codigo", "articulo_descripcion", metric])

    # filtramos por subrubro y clientes similares
    # candidate_clients es set de tuplas (cliente_id, RazonSocial, cuit)
    candidate_ids = {ck[0] for ck in candidate_clients}
    dfx = df[(df["subrubro"] == subrubro) & (df["cliente_id"].isin(candidate_ids))].copy()
    if dfx.empty:
        return pd.DataFrame(columns=["articulo_codigo", "articulo_descripcion", metric])

    agg = (
        dfx.groupby(["articulo_codigo", "articulo_descripcion"], as_index=False)
        .agg(
            importe=("importe", "sum"),
            unidades=("unidades", "sum"),
            pedidos=("cant_pedidos", "sum"),
        )
    )

    # orden
    if metric == "pedidos":
        agg = agg.sort_values(["pedidos", "importe"], ascending=False)
        agg = agg.rename(columns={"pedidos": "pedidos"})
    elif metric == "unidades":
        agg = agg.sort_values(["unidades", "importe"], ascending=False)
    else:
        agg = agg.sort_values(["importe", "unidades"], ascending=False)

    return agg.head(top_n)


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

st.title("🧺 Detector de Canastas Llenas")
st.caption("Prototipo de cross-selling por frecuencia / co-ocurrencia de subrubros (por cliente).")

uploaded = st.file_uploader("Subí tu CSV o Excel de ventas", type=["csv", "xlsx", "xls"])

if not uploaded:
    st.info("Subí un archivo para comenzar.")
    st.stop()

with st.spinner("Leyendo archivo..."):
    df = read_any_table(uploaded)

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Filas", f"{len(df):,}".replace(",", "."))
col2.metric("Clientes", f"{df['cliente_id'].nunique():,}".replace(",", "."))
col3.metric("Subrubros", f"{df['subrubro'].nunique():,}".replace(",", "."))

# índices
with st.spinner("Preparando índices..."):
    client_to_subs, sub_to_clients, cs_agg = build_indices(df)

# -----------------------------
# Punto 1 (ya): buscador + selector
# -----------------------------
st.markdown("---")
st.subheader("Buscar cliente")

search_text = st.text_input("Buscar por Razón Social / Código Cliente / CUIT", value="", placeholder="Ej: fridman, 000123, 2030...")

clients_df = (
    df[["cliente_id", "RazonSocial", "cuit"]]
    .drop_duplicates()
    .sort_values(["RazonSocial", "cliente_id"])
)

if search_text.strip():
    q = _normalize(search_text)
    mask = (
        clients_df["RazonSocial"].astype(str).apply(_normalize).str.contains(q, na=False)
        | clients_df["cliente_id"].astype(str).apply(_normalize).str.contains(q, na=False)
        | clients_df["cuit"].astype(str).apply(_normalize).str.contains(q, na=False)
    )
    filtered_clients = clients_df[mask].copy()
else:
    filtered_clients = clients_df.copy()

# para que no muestre 4.500 en el selector si no escribió nada
MAX_OPTIONS = 200
if len(filtered_clients) > MAX_OPTIONS and not search_text.strip():
    st.warning(f"Hay {len(filtered_clients)} clientes. Escribí algo arriba para filtrar (muestro los primeros {MAX_OPTIONS}).")
    filtered_clients = filtered_clients.head(MAX_OPTIONS)

options = [
    f"{r.RazonSocial} | ID {r.cliente_id} | CUIT {r.cuit}"
    for r in filtered_clients.itertuples(index=False)
]

selected_label = st.selectbox("Seleccioná un cliente", options=options, index=0 if options else None)

if not selected_label:
    st.stop()

# parse del label
# formato: "RS | ID xxx | CUIT yyy"
parts = [p.strip() for p in selected_label.split("|")]
rs = parts[0]
cid = parts[1].replace("ID", "").strip() if len(parts) > 1 else ""
cuit = parts[2].replace("CUIT", "").strip() if len(parts) > 2 else ""
client_key = (cid, rs, cuit)

# -----------------------------
# Vista cliente: subrubros que compra
# -----------------------------
st.markdown("---")
left, right = st.columns([1.05, 0.95], gap="large")

with left:
    st.subheader("📦 Subrubros que compra")

    df_client_sub = cs_agg[
        (cs_agg["cliente_id"] == cid) &
        (cs_agg["RazonSocial"] == rs) &
        (cs_agg["cuit"] == cuit)
    ].copy()

    if df_client_sub.empty:
        st.warning("No encontré compras para este cliente con el filtro actual.")
    else:
        show = df_client_sub.sort_values("importe", ascending=False).copy()
        show["importe"] = show["importe"].round(0)
        show["unidades"] = show["unidades"].round(0)
        show["pedidos"] = show["pedidos"].round(0)
        st.dataframe(show[["subrubro", "importe", "unidades", "pedidos"]], use_container_width=True, hide_index=True)

with right:
    st.subheader("💡 Sugerencias de Venta Cruzada (Top 10) + Productos (Punto 2)")

    metric = st.radio(
        "¿Cómo querés rankear los productos dentro de cada subrubro?",
        options=["importe", "unidades", "pedidos"],
        horizontal=True,
        index=0,
    )

    topk = st.slider("Cantidad de subrubros oportunidad", min_value=5, max_value=20, value=10, step=1)
    topn_prod = st.slider("Productos por subrubro", min_value=3, max_value=15, value=8, step=1)

    recs, candidate_clients, sim_map = recommend_subrubros(
        client_key=client_key,
        client_to_subs=client_to_subs,
        sub_to_clients=sub_to_clients,
        top_k=topk,
    )

    if not recs:
        st.info("No hay suficientes clientes similares para proponer oportunidades (o el cliente no tiene subrubros).")
    else:
        # tabla resumen de oportunidades
        opp_df = pd.DataFrame(recs, columns=["subrubro", "score_similitud"])
        st.dataframe(opp_df, use_container_width=True, hide_index=True)

        st.caption(
            "El score de similitud suma cuántos subrubros comparte este cliente con otros clientes que compran ese subrubro."
        )

        # Punto 2: dentro de cada subrubro, top productos
        st.markdown("#### 🧩 Productos sugeridos dentro de cada subrubro oportunidad")
        for subr, score in recs:
            with st.expander(f"{subr}  —  score {score}"):
                prod = top_products_for_subrubro(
                    df=df,
                    subrubro=subr,
                    candidate_clients=candidate_clients,
                    metric=metric,
                    top_n=topn_prod,
                )
                if prod.empty:
                    st.write("Sin datos de productos para este subrubro en clientes similares.")
                else:
                    # formato
                    prod_fmt = prod.copy()
                    for c in ["importe", "unidades", "pedidos"]:
                        if c in prod_fmt.columns:
                            prod_fmt[c] = prod_fmt[c].round(0)
                    st.dataframe(
                        prod_fmt[["articulo_codigo", "articulo_descripcion", "importe", "unidades", "pedidos"]],
                        use_container_width=True,
                        hide_index=True,
                    )

st.markdown("---")
st.caption(
    "Tip: si tus CUIT vienen con puntos/guiones, no pasa nada. El buscador normaliza y busca igual."
)
