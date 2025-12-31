import re
import unicodedata
from difflib import get_close_matches

import pandas as pd
import streamlit as st


# ----------------------------
# Helpers: normalización / fuzzy match
# ----------------------------
def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])  # sin acentos
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)  # todo a snake-ish
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def detect_columns(df: pd.DataFrame, expected_map: dict, threshold: float = 0.72):
    """
    expected_map: {canonical: [posibles nombres]}
    Devuelve mapping {canonical: col_real_en_df or None} y lista de warnings
    """
    cols = list(df.columns)
    norm_cols = {_normalize(c): c for c in cols}

    mapping = {}
    warnings = []

    for canonical, candidates in expected_map.items():
        # intentamos match directo normalizado
        found = None
        for cand in candidates:
            n = _normalize(cand)
            if n in norm_cols:
                found = norm_cols[n]
                break

        # si no hay directo, fuzzy
        if found is None:
            # armamos lista de strings comparables
            choices = list(norm_cols.keys())
            best = get_close_matches(_normalize(candidates[0]), choices, n=1, cutoff=threshold)
            if best:
                found = norm_cols[best[0]]

        mapping[canonical] = found
        if found is None:
            warnings.append(f"No pude detectar la columna para **{canonical}** (busqué: {candidates})")

    return mapping, warnings


# ----------------------------
# Carga de datos
# ----------------------------
@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        # intentamos utf-8, si falla latin-1
        try:
            df = pd.read_csv(
                uploaded_file,
                sep=",",
                dtype=str,
                encoding="utf-8",
                engine="python",
                on_bad_lines="skip",
            )
        except Exception:
            df = pd.read_csv(
                uploaded_file,
                sep=",",
                dtype=str,
                encoding="latin-1",
                engine="python",
                on_bad_lines="skip",
            )

    elif name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(uploaded_file, dtype=str)
    else:
        raise ValueError("Formato no soportado. Subí .csv o .xlsx")

    # limpiamos headers “raros”
    df.columns = [str(c).strip() for c in df.columns]

    return df


def to_numeric_series(s: pd.Series):
    # convierte "1.234,56" o "1234.56" a float
    if s is None:
        return None
    x = s.astype(str).str.replace(r"\s+", "", regex=True)
    x = x.str.replace(".", "", regex=False)  # saca separador miles
    x = x.str.replace(",", ".", regex=False)  # decimal coma -> punto
    return pd.to_numeric(x, errors="coerce").fillna(0.0)


# ----------------------------
# Motor de co-ocurrencia por subrubro
# ----------------------------
@st.cache_data(show_spinner=False)
def build_models(df: pd.DataFrame, col_cliente: str, col_razon: str, col_subrubro: str, col_pedidos: str):
    """
    Devuelve:
      - clientes_df: (cliente_id, RazonSocial) únicos
      - client_sub: tabla cliente-subrubro con peso (cant_pedidos)
      - cooc: matriz co-ocurrencia subrubro x subrubro (conteo de clientes)
      - subrubro_pop: popularidad subrubro (cantidad clientes)
    """

    # base mínima
    base = df[[col_cliente, col_razon, col_subrubro, col_pedidos]].copy()

    base[col_cliente] = base[col_cliente].astype(str).str.strip()
    base[col_razon] = base[col_razon].astype(str).str.strip()
    base[col_subrubro] = base[col_subrubro].astype(str).str.strip()

    # pedidos a num
    base[col_pedidos] = to_numeric_series(base[col_pedidos])

    # 1) catálogo clientes
    clientes_df = (
        base[[col_cliente, col_razon]]
        .dropna()
        .drop_duplicates()
        .rename(columns={col_cliente: "cliente_id", col_razon: "RazonSocial"})
        .sort_values(["RazonSocial", "cliente_id"])
    )

    # 2) cliente-subrubro (peso = cant_pedidos)
    client_sub = (
        base.groupby([col_cliente, col_subrubro], as_index=False)[col_pedidos]
        .sum()
        .rename(columns={col_cliente: "cliente_id", col_subrubro: "subrubro", col_pedidos: "peso"})
    )

    # 3) co-ocurrencia por cliente (binaria: compró/no)
    #    armamos sets por cliente
    sub_by_client = client_sub.groupby("cliente_id")["subrubro"].apply(list)

    # conteo clientes por subrubro
    subrubro_pop = client_sub.groupby("subrubro")["cliente_id"].nunique().sort_values(ascending=False)

    # cooc: para cada cliente, sumamos pares de subrubros
    # enfoque eficiente: generar pares dentro de cada lista
    from collections import Counter
    pair_counter = Counter()

    for subs in sub_by_client:
        uniq = sorted(set([s for s in subs if s and s.lower() != "nan"]))
        n = len(uniq)
        if n < 2:
            continue
        for i in range(n):
            for j in range(i + 1, n):
                pair_counter[(uniq[i], uniq[j])] += 1

    # convertimos a DataFrame largo
    if pair_counter:
        pairs = pd.DataFrame(
            [(a, b, c) for (a, b), c in pair_counter.items()],
            columns=["a", "b", "clientes_en_comun"],
        )
    else:
        pairs = pd.DataFrame(columns=["a", "b", "clientes_en_comun"])

    return clientes_df, client_sub, pairs, subrubro_pop


def recommend_for_client(client_id: str, client_sub: pd.DataFrame, pairs: pd.DataFrame, top_k: int = 5):
    """
    Recomendación por cliente:
      - toma subrubros que compra
      - busca subrubros que más co-ocurren con esos (por conteo clientes_en_comun)
      - excluye los ya comprados
    """
    bought = set(client_sub.loc[client_sub["cliente_id"] == client_id, "subrubro"].dropna().tolist())
    bought = set([b for b in bought if str(b).strip() and str(b).lower() != "nan"])

    if not bought:
        return bought, pd.DataFrame(columns=["subrubro_recomendado", "score_clientes_en_comun"])

    # armamos score sumando co-ocurrencias contra todo lo que compra
    from collections import defaultdict
    score = defaultdict(float)

    # pairs está con a<b
    for _, row in pairs.iterrows():
        a = row["a"]
        b = row["b"]
        c = float(row["clientes_en_comun"])
        if a in bought and b not in bought:
            score[b] += c
        elif b in bought and a not in bought:
            score[a] += c

    rec = pd.DataFrame(
        [(k, v) for k, v in score.items()],
        columns=["subrubro_recomendado", "score_clientes_en_comun"],
    ).sort_values("score_clientes_en_comun", ascending=False)

    return bought, rec.head(top_k)


def recommend_for_subrubro(subrubro: str, pairs: pd.DataFrame, top_k: int = 20):
    """
    Dado un subrubro, muestra con cuáles se combina más.
    """
    sub = str(subrubro).strip()
    if not sub:
        return pd.DataFrame(columns=["subrubro", "clientes_en_comun"])

    mask = (pairs["a"] == sub) | (pairs["b"] == sub)
    tmp = pairs.loc[mask].copy()
    if tmp.empty:
        return pd.DataFrame(columns=["subrubro", "clientes_en_comun"])

    tmp["subrubro"] = tmp.apply(lambda r: r["b"] if r["a"] == sub else r["a"], axis=1)
    out = tmp[["subrubro", "clientes_en_comun"]].sort_values("clientes_en_comun", ascending=False)
    return out.head(top_k)


# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

st.title("🧺 Detector de Canastas Llenas")
st.caption("Prototipo: usa co-ocurrencia por cliente para sugerir cross-sell **solo por subrubro** (frecuencia).")

with st.sidebar:
    st.header("Datos")
    st.write("Cargá tu CSV (separador coma).")

    uploaded = st.file_uploader("Subí tu archivo", type=["csv", "xlsx", "xls"])
    st.divider()

    st.subheader("Buscar por")
    mode = st.radio("Modo", ["Cliente", "Subrubro"], index=0)

    st.divider()
    st.info("Tip: si el archivo es grande, la primera carga puede tardar unos segundos.")


# Si no carga, mostramos un aviso claro
if not uploaded:
    st.warning("Subí un archivo para empezar (CSV o Excel).")
    st.stop()

# 1) Cargar
df_raw = load_data(uploaded)

# 2) Detectar columnas
expected = {
    "cliente_id": ["cliente_id", "cliente_codigo", "codigo_cliente", "id_cliente", "cliente"],
    "RazonSocial": ["RazonSocial", "razon_social", "razon", "cliente_nombre", "nombre_cliente"],
    "subrubro": ["subrubro", "Articulo Sub Rubro", "articulo_sub_rubro", "sub_rubro", "sub rubro"],
    "cant_pedidos": ["cant_pedidos", "cant pedidos", "Cantidad Pedidos", "pedidos", "cant_pedido"],
}

mapping, warns = detect_columns(df_raw, expected)

# 3) Mostrar diagnóstico arriba
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Filas", f"{len(df_raw):,}".replace(",", "."))
with col2:
    st.metric("Columnas", f"{len(df_raw.columns)}")
with col3:
    st.metric("Archivo", uploaded.name)

with st.expander("🔎 Diagnóstico de columnas detectadas", expanded=True):
    st.write("Columnas del archivo:")
    st.code(", ".join(df_raw.columns))
    st.write("Mapping detectado:")
    st.json(mapping)
    if warns:
        st.error("Faltan columnas mínimas para funcionar:")
        for w in warns:
            st.write("- " + w)
        st.stop()
    else:
        st.success("OK: pude detectar las columnas mínimas.")

# 4) Construir modelos
clientes_df, client_sub, pairs, subrubro_pop = build_models(
    df_raw,
    col_cliente=mapping["cliente_id"],
    col_razon=mapping["RazonSocial"],
    col_subrubro=mapping["subrubro"],
    col_pedidos=mapping["cant_pedidos"],
)

# 5) Métricas
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Clientes", f"{clientes_df['cliente_id'].nunique():,}".replace(",", "."))
with c2:
    st.metric("Subrubros", f"{client_sub['subrubro'].nunique():,}".replace(",", "."))
with c3:
    st.metric("Pares con co-ocurrencia", f"{len(pairs):,}".replace(",", "."))

st.divider()

# ----------------------------
# MODO CLIENTE
# ----------------------------
if mode == "Cliente":
    st.subheader("Buscar por cliente")

    # Buscador: por razon o por id (texto)
    # Armamos opciones legibles
    clientes_df["label"] = clientes_df["cliente_id"].astype(str) + " — " + clientes_df["RazonSocial"].astype(str)

    selected = st.selectbox(
        "Cliente (podés tipear razón social o el código)",
        options=clientes_df["label"].tolist(),
        index=None,
        placeholder="Elegí un cliente…",
    )

    if not selected:
        st.stop()

    client_id = selected.split("—")[0].strip()

    bought, rec = recommend_for_client(client_id, client_sub, pairs, top_k=5)

    left, right = st.columns([1, 1])

    with left:
        st.markdown("### 🧾 Subrubros que compra")
        bought_df = (
            client_sub[client_sub["cliente_id"] == client_id]
            .groupby("subrubro", as_index=False)["peso"]
            .sum()
            .sort_values("peso", ascending=False)
            .rename(columns={"peso": "cant_pedidos"})
        )
        st.dataframe(bought_df, use_container_width=True, height=420)

    with right:
        st.markdown("### 💡 Sugerencias de Venta Cruzada (Top 5)")
        if rec.empty:
            st.info("No hay suficientes co-ocurrencias para sugerir cross-sell con este cliente.")
        else:
            st.dataframe(rec, use_container_width=True, height=420)

# ----------------------------
# MODO SUBRUBRO
# ----------------------------
else:
    st.subheader("Buscar por subrubro")

    sub_options = subrubro_pop.index.tolist()
    sel_sub = st.selectbox(
        "Subrubro",
        options=sub_options,
        index=None,
        placeholder="Elegí un subrubro…",
    )

    if not sel_sub:
        st.stop()

    st.markdown("### 🔗 Subrubros que más se combinan con este (Top 20)")
    out = recommend_for_subrubro(sel_sub, pairs, top_k=20)
    if out.empty:
        st.info("No hay co-ocurrencias suficientes para este subrubro.")
    else:
        st.dataframe(out, use_container_width=True, height=520)

    st.markdown("### 📈 Popularidad del subrubro (cantidad de clientes que lo compran)")
    st.write(int(subrubro_pop.get(sel_sub, 0)))
