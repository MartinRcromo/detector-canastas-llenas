import io
import re
import unicodedata
from collections import defaultdict

import pandas as pd
import streamlit as st


# -----------------------------
# Helpers
# -----------------------------
def _normalize(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s


def read_csv_with_fallback(uploaded_file) -> pd.DataFrame:
    """
    Streamlit uploader entrega un file-like. Leemos bytes y probamos encodings típicos de Excel/Windows.
    """
    raw = uploaded_file.getvalue()
    encodings_to_try = ["utf-8", "utf-8-sig", "cp1252", "latin1"]

    last_err = None
    for enc in encodings_to_try:
        try:
            bio = io.BytesIO(raw)
            df = pd.read_csv(
                bio,
                sep=",",
                encoding=enc,
                dtype=str,              # primero todo texto para evitar errores
                on_bad_lines="skip",    # por si hay alguna línea rota
                engine="python",
            )
            df.attrs["detected_encoding"] = enc
            return df
        except Exception as e:
            last_err = e

    raise last_err


def cooccurrence_rules_by_client(df: pd.DataFrame, col_client: str, col_subrubro: str):
    """
    Devuelve:
      - rules[(a,b)] = cantidad de clientes que compraron ambos subrubros a y b
      - support[a]   = cantidad de clientes que compraron el subrubro a
    """
    client_to_subs = defaultdict(set)

    for _, row in df[[col_client, col_subrubro]].dropna().iterrows():
        c = str(row[col_client]).strip()
        s = str(row[col_subrubro]).strip()
        if c and s:
            client_to_subs[c].add(s)

    support = defaultdict(int)
    pair_count = defaultdict(int)

    for c, subs in client_to_subs.items():
        subs = sorted(subs)
        for a in subs:
            support[a] += 1
        # pares
        for i in range(len(subs)):
            for j in range(i + 1, len(subs)):
                pair_count[(subs[i], subs[j])] += 1

    # para consulta fácil en ambos sentidos
    rules = defaultdict(int)
    for (a, b), cnt in pair_count.items():
        rules[(a, b)] = cnt
        rules[(b, a)] = cnt

    return rules, support, client_to_subs


def safe_to_numeric(series: pd.Series) -> pd.Series:
    # Convierte "1.234,56" o "1234,56" o "1234.56" a float de forma robusta
    s = series.fillna("").astype(str).str.strip()
    s = s.str.replace(" ", "", regex=False)
    # si viene estilo AR: miles con punto y decimales con coma
    # sacamos miles y pasamos coma a punto
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Detector de Canastas Llenas", layout="wide")

st.title("🧺 Detector de Canastas Llenas")
st.caption("Prototipo de cross-selling por **frecuencia de co-ocurrencia** de subrubros (por cliente).")

with st.sidebar:
    st.header("Datos")
    st.write("Subí un CSV (coma `,`). Si el archivo viene de Excel, puede estar en cp1252/latin1: esta app lo detecta.")
    uploaded = st.file_uploader("Subí tu archivo", type=["csv"])

    st.divider()
    st.header("Parámetros")
    top_k = st.number_input("Cantidad de sugerencias", min_value=1, max_value=20, value=5, step=1)
    min_support = st.number_input("Mínimo clientes (support) para sugerir un subrubro", min_value=1, max_value=5000, value=5, step=1)


# -----------------------------
# Load Data
# -----------------------------
if not uploaded:
    st.info("Subí un CSV para empezar.")
    st.stop()

try:
    df_raw = read_csv_with_fallback(uploaded)
    detected = df_raw.attrs.get("detected_encoding", "desconocido")
except Exception as e:
    st.error("No pude leer el CSV. Probá guardarlo como **CSV UTF-8** desde Excel y re-subilo.")
    st.exception(e)
    st.stop()

# Normalizamos nombres de columnas (por si vienen con espacios raros)
df = df_raw.copy()
df.columns = [str(c).strip() for c in df.columns]

required = [
    "empresa", "anio_mes", "cliente_id", "cuit", "RazonSocial", "localidad", "vendedor", "zona_comercial",
    "subrubro", "articulo_codigo", "articulo_descripcion", "unidades", "importe", "cant_pedidos"
]
missing = [c for c in required if c not in df.columns]

if missing:
    st.error("Faltan columnas requeridas en tu CSV:")
    st.write(missing)
    st.write("Columnas encontradas:")
    st.write(list(df.columns))
    st.stop()

# Cast / limpieza básica
df["cliente_id"] = df["cliente_id"].astype(str).str.strip()
df["RazonSocial"] = df["RazonSocial"].astype(str).str.strip()
df["subrubro"] = df["subrubro"].astype(str).str.strip()

df["unidades_num"] = safe_to_numeric(df["unidades"])
df["importe_num"] = safe_to_numeric(df["importe"])
df["cant_pedidos_num"] = safe_to_numeric(df["cant_pedidos"])

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Filas", f"{len(df):,}".replace(",", "."))
c2.metric("Clientes", f"{df['cliente_id'].nunique():,}".replace(",", "."))
c3.metric("Subrubros", f"{df['subrubro'].nunique():,}".replace(",", "."))
c4.metric("Encoding leído", detected)

st.divider()

# Precompute co-ocurrencias
with st.spinner("Calculando co-ocurrencias de subrubros por cliente..."):
    rules, support, client_to_subs = cooccurrence_rules_by_client(df, "cliente_id", "subrubro")

# Selector modo búsqueda
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Buscar por")
    mode = st.radio("", ["Cliente", "Subrubro"], horizontal=False)

with col_right:
    if mode == "Cliente":
        st.subheader("Buscar por cliente")

        # lista de clientes con label
        clients = (
            df[["cliente_id", "RazonSocial"]]
            .drop_duplicates()
            .assign(label=lambda x: x["cliente_id"].astype(str) + " — " + x["RazonSocial"].astype(str))
            .sort_values("label")
        )

        selected = st.selectbox("Cliente (podés tipear razón social)", options=clients["label"].tolist())
        sel_id = selected.split(" — ")[0].strip()

        # subrubros del cliente
        subs = sorted(list(client_to_subs.get(sel_id, set())))
        if not subs:
            st.warning("Este cliente no tiene subrubros asociados (o quedó vacío tras limpieza).")
            st.stop()

        s1, s2 = st.columns(2)

        with s1:
            st.markdown("### 🧾 Subrubros que compra")
            # tabla por ranking de importe / unidades
            tmp = (
                df[df["cliente_id"] == sel_id]
                .groupby("subrubro", as_index=False)
                .agg(
                    importe=("importe_num", "sum"),
                    unidades=("unidades_num", "sum"),
                    pedidos=("cant_pedidos_num", "sum"),
                )
                .sort_values(["importe", "pedidos", "unidades"], ascending=False)
            )
            st.dataframe(tmp, use_container_width=True, height=360)

        with s2:
            st.markdown(f"### 💡 Sugerencias de Venta Cruzada (Top {top_k})")

            # score: sum co-ocurrencia con subrubros comprados
            scores = defaultdict(int)
            for a in subs:
                for b in support.keys():
                    if b == a:
                        continue
                    scores[b] += rules.get((a, b), 0)

            # sacamos los que ya compra
            for a in subs:
                scores.pop(a, None)

            # filtramos por support mínimo
            candidates = []
            for b, sc in scores.items():
                if support.get(b, 0) >= int(min_support) and sc > 0:
                    candidates.append((b, sc, support.get(b, 0)))

            candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
            top = candidates[: int(top_k)]

            if not top:
                st.info("No hay sugerencias con los filtros actuales. Probá bajar el mínimo de support.")
            else:
                out = pd.DataFrame(top, columns=["Subrubro sugerido", "Score co-ocurrencia", "Clientes que lo compran"])
                st.dataframe(out, use_container_width=True, height=360)

                # bonus: mostrar artículos más comprados de esos subrubros (para proponer)
                st.markdown("#### 🧩 Artículos top dentro de los subrubros sugeridos")
                suggested_subs = [x[0] for x in top]
                art = (
                    df[df["subrubro"].isin(suggested_subs)]
                    .groupby(["subrubro", "articulo_codigo", "articulo_descripcion"], as_index=False)
                    .agg(
                        importe=("importe_num", "sum"),
                        unidades=("unidades_num", "sum"),
                        pedidos=("cant_pedidos_num", "sum"),
                    )
                    .sort_values(["subrubro", "importe", "pedidos"], ascending=[True, False, False])
                )
                # top 5 por subrubro
                art["rank"] = art.groupby("subrubro")["importe"].rank(method="first", ascending=False)
                art = art[art["rank"] <= 5].drop(columns=["rank"])
                st.dataframe(art, use_container_width=True, height=360)

    else:
        st.subheader("Buscar por subrubro")
        subs_all = sorted(df["subrubro"].dropna().unique().tolist())
        sel_sub = st.selectbox("Subrubro", options=subs_all)

        # clientes que compran ese subrubro
        buyers = df[df["subrubro"] == sel_sub]["cliente_id"].unique().tolist()

        st.markdown("### 💡 Cross-sell sugerido para este subrubro")
        # sugerimos subrubros que co-ocurren con este
        cand = []
        for b in support.keys():
            if b == sel_sub:
                continue
            sc = rules.get((sel_sub, b), 0)
            if sc > 0 and support.get(b, 0) >= int(min_support):
                cand.append((b, sc, support.get(b, 0)))

        cand.sort(key=lambda x: (x[1], x[2]), reverse=True)
        top = cand[: int(top_k)]

        if not top:
            st.info("No hay sugerencias con los filtros actuales. Probá bajar el mínimo de support.")
        else:
            out = pd.DataFrame(top, columns=["Subrubro sugerido", "Clientes en común", "Clientes que lo compran"])
            st.dataframe(out, use_container_width=True, height=320)

        st.markdown("### 🧾 Clientes que compran este subrubro (muestra)")
        sample = (
            df[df["subrubro"] == sel_sub][["cliente_id", "RazonSocial", "localidad", "zona_comercial", "vendedor"]]
            .drop_duplicates()
            .head(200)
        )
        st.dataframe(sample, use_container_width=True, height=360)
