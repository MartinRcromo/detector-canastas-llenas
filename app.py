import re
import unicodedata
from difflib import get_close_matches
from itertools import combinations

import pandas as pd
import streamlit as st


# =========================
# Helpers (normalización)
# =========================
def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9_ ]", "", s)
    return s


def _pick_column(df: pd.DataFrame, desired: str, aliases: list[str]) -> str | None:
    """
    Intenta encontrar una columna que matchee desired/aliases
    usando normalización y fuzzy match.
    """
    cols = list(df.columns)
    norm_map = {_normalize(c): c for c in cols}

    # match exacto por desired o alias
    candidates = [desired] + aliases
    for cand in candidates:
        n = _normalize(cand)
        if n in norm_map:
            return norm_map[n]

    # fuzzy match
    desired_norms = [_normalize(c) for c in candidates]
    best = None
    best_score = 0.0
    for col in cols:
        coln = _normalize(col)
        # busca parecido contra todos los desired_norms
        matches = get_close_matches(coln, desired_norms, n=1, cutoff=0.75)
        if matches:
            # score aprox: longitud match / longitud col
            score = min(1.0, len(matches[0]) / max(1, len(coln)))
            if score > best_score:
                best_score = score
                best = col
    return best


def _safe_read_csv(uploaded_file) -> pd.DataFrame:
    """
    Lee CSV con fallback de encoding y separador.
    """
    # en Streamlit, uploaded_file es BytesIO-like
    # probamos encodings comunes en Argentina/Excel
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    last_err = None

    for enc in encodings:
        try:
            uploaded_file.seek(0)
            # sep=None + engine python detecta delimitador,
            # pero como vos confirmaste coma, lo fijamos en ",".
            df = pd.read_csv(uploaded_file, sep=",", encoding=enc, low_memory=False)
            return df
        except Exception as e:
            last_err = e

    # último intento: autodetect delimiter
    for enc in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=None, engine="python", encoding=enc, low_memory=False)
            return df
        except Exception as e:
            last_err = e

    raise last_err


# =========================
# Lógica cross-sell
# =========================
@st.cache_data(show_spinner=False)
def build_rules(df: pd.DataFrame, cliente_col: str, subrubro_col: str, weight_col: str | None):
    """
    Construye reglas simples de co-ocurrencia por cliente:
    - Para cada cliente: set subrubros comprados
    - Para cada par (A,B): cuenta co-ocurrencia
    Retorna:
      client_subrubros: dict[cliente -> set(subrubros)]
      pair_counts: dict[(A,B)->count]
      subrubro_popularity: Series subrubro -> score (unidades/importe/cant_pedidos o 1)
    """
    d = df[[cliente_col, subrubro_col]].copy()
    d[cliente_col] = d[cliente_col].astype(str)

    # limpieza básica
    d[subrubro_col] = d[subrubro_col].astype(str).str.strip()
    d = d[(d[subrubro_col] != "") & (d[subrubro_col].notna())]

    # Popularidad (para ordenar sugerencias)
    if weight_col and weight_col in df.columns:
        pop = df.groupby(subrubro_col)[weight_col].sum().sort_values(ascending=False)
    else:
        pop = df.groupby(subrubro_col).size().sort_values(ascending=False)

    # Subrubros por cliente
    grp = d.groupby(cliente_col)[subrubro_col].apply(lambda x: set(x.unique()))
    client_subrubros = grp.to_dict()

    # Co-ocurrencia por pares
    pair_counts = {}
    for _, subs in client_subrubros.items():
        if len(subs) < 2:
            continue
        for a, b in combinations(sorted(subs), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    return client_subrubros, pair_counts, pop


def suggest_cross_sell_for_client(
    cliente_key: str,
    client_subrubros: dict,
    pair_counts: dict,
    popularity: pd.Series,
    top_n: int = 10,
):
    """
    Dado un cliente, recomienda subrubros NO comprados, usando:
      score = suma co-ocurrencias con los subrubros que sí compra
      desempate por popularidad global
    """
    bought = client_subrubros.get(cliente_key, set())
    if not bought:
        return pd.DataFrame(columns=["subrubro_sugerido", "score_coocurrencia", "popularidad_global"])

    scores = {}
    for (a, b), c in pair_counts.items():
        if a in bought and b not in bought:
            scores[b] = scores.get(b, 0) + c
        elif b in bought and a not in bought:
            scores[a] = scores.get(a, 0) + c

    if not scores:
        return pd.DataFrame(columns=["subrubro_sugerido", "score_coocurrencia", "popularidad_global"])

    rows = []
    for sub, sc in scores.items():
        pop = float(popularity.get(sub, 0))
        rows.append((sub, sc, pop))

    out = pd.DataFrame(rows, columns=["subrubro_sugerido", "score_coocurrencia", "popularidad_global"])
    out = out.sort_values(["score_coocurrencia", "popularidad_global"], ascending=[False, False]).head(top_n)
    return out


# =========================
# UI
# =========================
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

st.title("🧺 Detector de Canastas Llenas")
st.caption("Prototipo de cross-selling por frecuencia / co-ocurrencia de subrubros (por cliente).")

with st.sidebar:
    st.header("Datos")
    st.write("Subí tu CSV de ventas (separado por coma).")
    uploaded = st.file_uploader("Subí tu archivo", type=["csv"])
    top_n = st.slider("Cantidad de sugerencias (Top N)", 5, 30, 10, 1)

# Si no hay archivo, no seguimos
if not uploaded:
    st.info("Subí un CSV para comenzar.")
    st.stop()

# Cargar CSV robusto
try:
    df = _safe_read_csv(uploaded)
except Exception as e:
    st.error("No pude leer el CSV. Probá guardarlo como CSV UTF-8 desde Excel.")
    st.exception(e)
    st.stop()

# Detectar columnas necesarias
col_cliente_id = _pick_column(df, "cliente_id", ["cliente", "codigo_cliente", "cliente_codigo", "id_cliente"])
col_cuit = _pick_column(df, "cuit", ["cuil", "tax_id"])
col_razon = _pick_column(df, "RazonSocial", ["razon_social", "razon", "cliente_nombre", "nombre_cliente"])
col_subrubro = _pick_column(df, "subrubro", ["articulo_sub_rubro", "sub_rubro", "sub rubro", "subrubro_nombre"])
col_unidades = _pick_column(df, "unidades", ["cantidad", "qty"])
col_importe = _pick_column(df, "importe", ["importe $", "monto", "total", "importe_pesos"])
col_cant_pedidos = _pick_column(df, "cant_pedidos", ["cantidad_pedidos", "n_pedidos", "cant pedidos", "pedidos"])

required = {
    "cliente_id": col_cliente_id,
    "RazonSocial": col_razon,
    "subrubro": col_subrubro,
}
missing = [k for k, v in required.items() if v is None]

if missing:
    st.error("Faltan columnas necesarias en tu archivo.")
    st.write("Necesito al menos: **cliente_id**, **RazonSocial**, **subrubro**.")
    st.write("Columnas encontradas:", list(df.columns))
    st.write("No encontré:", missing)
    st.stop()

# Renombrar a estándar para trabajar cómodo
rename_map = {}
if col_cliente_id: rename_map[col_cliente_id] = "cliente_id"
if col_cuit: rename_map[col_cuit] = "cuit"
if col_razon: rename_map[col_razon] = "RazonSocial"
if col_subrubro: rename_map[col_subrubro] = "subrubro"
if col_unidades: rename_map[col_unidades] = "unidades"
if col_importe: rename_map[col_importe] = "importe"
if col_cant_pedidos: rename_map[col_cant_pedidos] = "cant_pedidos"

df = df.rename(columns=rename_map)

# Normalización mínima de tipos
df["cliente_id"] = df["cliente_id"].astype(str).str.strip()
df["RazonSocial"] = df["RazonSocial"].astype(str).str.strip()
df["subrubro"] = df["subrubro"].astype(str).str.strip()

if "cuit" in df.columns:
    df["cuit"] = df["cuit"].astype(str).str.strip()

for num_col in ["unidades", "importe", "cant_pedidos"]:
    if num_col in df.columns:
        df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)

# Métricas arriba
c1, c2, c3 = st.columns(3)
c1.metric("Filas", f"{len(df):,}".replace(",", "."))
c2.metric("Clientes", f"{df['cliente_id'].nunique():,}".replace(",", "."))
c3.metric("Subrubros", f"{df['subrubro'].nunique():,}".replace(",", "."))

st.divider()

# =========================
# ✅ MEJORA #1: Buscador de cliente (por id/cuit/razón)
# =========================
st.subheader("Buscar cliente")

# pre-armamos una tabla única de clientes (más liviana)
clientes_cols = ["cliente_id", "RazonSocial"]
if "cuit" in df.columns:
    clientes_cols.append("cuit")

df_clientes = df[clientes_cols].drop_duplicates().copy()
df_clientes["RazonSocial_norm"] = df_clientes["RazonSocial"].map(_normalize)
df_clientes["cliente_id_norm"] = df_clientes["cliente_id"].map(_normalize)
if "cuit" in df_clientes.columns:
    df_clientes["cuit_norm"] = df_clientes["cuit"].map(_normalize)

busqueda = st.text_input(
    "Buscar por Razón Social / Código Cliente / CUIT",
    value="",
    placeholder="Ej: 000002  |  3069...  |  A Y B Repuestos",
)

# Filtrado dinámico (si no escribe nada, mostramos top 200 por frecuencia)
if busqueda.strip():
    b = _normalize(busqueda)
    mask = df_clientes["RazonSocial_norm"].str.contains(b, na=False) | df_clientes["cliente_id_norm"].str.contains(b, na=False)
    if "cuit_norm" in df_clientes.columns:
        mask = mask | df_clientes["cuit_norm"].str.contains(b, na=False)
    opciones = df_clientes[mask].copy()
else:
    # top clientes por cant_pedidos (si existe) o por unidades/importe
    if "cant_pedidos" in df.columns:
        top = df.groupby(["cliente_id", "RazonSocial"])["cant_pedidos"].sum().sort_values(ascending=False).head(200).reset_index()
    elif "unidades" in df.columns:
        top = df.groupby(["cliente_id", "RazonSocial"])["unidades"].sum().sort_values(ascending=False).head(200).reset_index()
    elif "importe" in df.columns:
        top = df.groupby(["cliente_id", "RazonSocial"])["importe"].sum().sort_values(ascending=False).head(200).reset_index()
    else:
        top = df_clientes.head(200)

    opciones = top.merge(df_clientes, on=["cliente_id", "RazonSocial"], how="left")

# armamos label lindo
def _label(row):
    if "cuit" in row and pd.notna(row["cuit"]) and str(row["cuit"]).strip() != "":
        return f"{row['RazonSocial']}  |  ID {row['cliente_id']}  |  CUIT {row['cuit']}"
    return f"{row['RazonSocial']}  |  ID {row['cliente_id']}"

if len(opciones) == 0:
    st.warning("No encontré clientes con esa búsqueda. Probá con menos letras o con el código.")
    st.stop()

opciones = opciones.drop_duplicates(subset=["cliente_id", "RazonSocial"]).copy()
opciones["label"] = opciones.apply(_label, axis=1)

cliente_label = st.selectbox(
    "Seleccioná un cliente",
    opciones["label"].tolist(),
    index=0,
)

# obtenemos cliente_id seleccionado
row_sel = opciones[opciones["label"] == cliente_label].iloc[0]
cliente_id_seleccionado = str(row_sel["cliente_id"])

st.caption(f"Cliente seleccionado: **{row_sel['RazonSocial']}** (ID: **{cliente_id_seleccionado}**)")

st.divider()

# =========================
# Filtrado por cliente
# =========================
df_cliente = df[df["cliente_id"] == cliente_id_seleccionado].copy()

# Elegimos weight para popularidad y co-ocurrencia (cant_pedidos > unidades > importe)
weight = None
if "cant_pedidos" in df.columns:
    weight = "cant_pedidos"
elif "unidades" in df.columns:
    weight = "unidades"
elif "importe" in df.columns:
    weight = "importe"

with st.spinner("Calculando reglas de cross-sell..."):
    client_subrubros, pair_counts, popularity = build_rules(df, "cliente_id", "subrubro", weight)

# =========================
# Subrubros que compra
# =========================
st.header("📦 Subrubros que compra")

agg_cols = []
if "cant_pedidos" in df_cliente.columns:
    agg_cols.append(("cant_pedidos", "sum"))
if "unidades" in df_cliente.columns:
    agg_cols.append(("unidades", "sum"))
if "importe" in df_cliente.columns:
    agg_cols.append(("importe", "sum"))

if agg_cols:
    grouped = df_cliente.groupby("subrubro").agg(**{k: (k, fn) for k, fn in agg_cols}).reset_index()
    # ordenar por la mejor métrica disponible
    if "cant_pedidos" in grouped.columns:
        grouped = grouped.sort_values("cant_pedidos", ascending=False)
    elif "unidades" in grouped.columns:
        grouped = grouped.sort_values("unidades", ascending=False)
    elif "importe" in grouped.columns:
        grouped = grouped.sort_values("importe", ascending=False)

    st.dataframe(grouped, use_container_width=True, height=340)
else:
    st.dataframe(df_cliente[["subrubro"]].drop_duplicates(), use_container_width=True)

# =========================
# Sugerencias de Cross-Sell
# =========================
st.header("💡 Sugerencias de Cross-Sell (subrubros)")

sug = suggest_cross_sell_for_client(
    cliente_key=cliente_id_seleccionado,
    client_subrubros=client_subrubros,
    pair_counts=pair_counts,
    popularity=popularity,
    top_n=top_n,
)

if sug.empty:
    st.info("No encontré sugerencias (puede pasar si el cliente compra muy pocos subrubros o no hay co-ocurrencia).")
else:
    st.dataframe(sug, use_container_width=True, height=300)

st.caption("Siguiente mejora (cuando me digas): resultados con *quick wins*, filtros por zona/vendedor y sugerencias de productos top dentro de cada subrubro.")
