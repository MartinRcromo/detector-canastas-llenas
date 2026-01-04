"""
Servicio de benchmark y análisis de co-ocurrencia
Identifica oportunidades de cross-selling basado en clientes similares
"""
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
from database import get_supabase

# Empresas del grupo para análisis
EMPRESAS_GRUPO = ["CANASATA", "SURTIHOGAR"]

def obtener_clientes_similares(
    cuit_objetivo: str,
    facturacion_min: float = None,
    facturacion_max: float = None,
    top_n: int = 50
) -> List[str]:
    """
    Encuentra clientes similares al objetivo basado en facturación

    Args:
        cuit_objetivo: CUIT del cliente a analizar
        facturacion_min: Facturación mínima del rango (si None, usa 70% del cliente)
        facturacion_max: Facturación máxima del rango (si None, usa 130% del cliente)
        top_n: Cantidad máxima de clientes similares a retornar

    Returns:
        Lista de CUITs de clientes similares
    """
    supabase = get_supabase()
    fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Obtener facturación del cliente objetivo
    response_objetivo = supabase.table("ventas") \
        .select("monto") \
        .eq("cuit", cuit_objetivo) \
        .gte("fecha", fecha_12_meses) \
        .in_("empresa", EMPRESAS_GRUPO) \
        .execute()

    if not response_objetivo.data:
        return []

    facturacion_objetivo = sum(v.get("monto", 0) for v in response_objetivo.data)

    # Definir rango de facturación
    if facturacion_min is None:
        facturacion_min = facturacion_objetivo * 0.7
    if facturacion_max is None:
        facturacion_max = facturacion_objetivo * 1.3

    # Obtener todos los clientes y su facturación
    response_todos = supabase.table("ventas") \
        .select("cuit, cliente, monto") \
        .gte("fecha", fecha_12_meses) \
        .in_("empresa", EMPRESAS_GRUPO) \
        .neq("cuit", cuit_objetivo) \
        .execute()

    if not response_todos.data:
        return []

    # Agrupar por CUIT y calcular facturación
    df = pd.DataFrame(response_todos.data)
    facturacion_por_cliente = df.groupby("cuit")["monto"].sum().reset_index()
    facturacion_por_cliente.columns = ["cuit", "facturacion"]

    # Filtrar por rango de facturación
    clientes_similares = facturacion_por_cliente[
        (facturacion_por_cliente["facturacion"] >= facturacion_min) &
        (facturacion_por_cliente["facturacion"] <= facturacion_max)
    ]

    # Ordenar por similitud (más cercano a facturación objetivo) y tomar top_n
    clientes_similares["diferencia"] = abs(
        clientes_similares["facturacion"] - facturacion_objetivo
    )
    clientes_similares = clientes_similares.sort_values("diferencia").head(top_n)

    return clientes_similares["cuit"].tolist()


def calcular_matriz_coocurrencia(cuits: List[str]) -> pd.DataFrame:
    """
    Calcula la matriz de co-ocurrencia de subrubros para un conjunto de clientes

    Args:
        cuits: Lista de CUITs a analizar

    Returns:
        DataFrame con la matriz de co-ocurrencia (subrubro x subrubro)
    """
    supabase = get_supabase()
    fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Obtener todas las compras de estos clientes
    response = supabase.table("ventas") \
        .select("cuit, subrubro") \
        .in_("cuit", cuits) \
        .gte("fecha", fecha_12_meses) \
        .in_("empresa", EMPRESAS_GRUPO) \
        .execute()

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    # Obtener subrubros únicos por cliente
    subrubros_por_cliente = df.groupby("cuit")["subrubro"].apply(set).reset_index()

    # Calcular co-ocurrencias
    subrubros_unicos = df["subrubro"].unique()
    matriz = pd.DataFrame(0, index=subrubros_unicos, columns=subrubros_unicos)

    for _, row in subrubros_por_cliente.iterrows():
        subrubros = list(row["subrubro"])
        for i, sub1 in enumerate(subrubros):
            for sub2 in subrubros[i:]:
                if sub1 != sub2:
                    matriz.loc[sub1, sub2] += 1
                    matriz.loc[sub2, sub1] += 1

    return matriz


def identificar_oportunidades(
    cuit_objetivo: str,
    min_coocurrencia: int = 5,
    top_familias: int = 4
) -> List[Dict]:
    """
    Identifica oportunidades de cross-selling para un cliente

    Args:
        cuit_objetivo: CUIT del cliente
        min_coocurrencia: Mínima co-ocurrencia para considerar una oportunidad
        top_familias: Cantidad de familias top a retornar

    Returns:
        Lista de oportunidades con formato:
        {
            "familia": str,
            "razon": str,
            "score": float,
            "coocurrencia": int
        }
    """
    supabase = get_supabase()
    fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # 1. Obtener subrubros que el cliente YA compra
    response_cliente = supabase.table("ventas") \
        .select("subrubro") \
        .eq("cuit", cuit_objetivo) \
        .gte("fecha", fecha_12_meses) \
        .in_("empresa", EMPRESAS_GRUPO) \
        .execute()

    if not response_cliente.data:
        return []

    subrubros_cliente = set(v.get("subrubro") for v in response_cliente.data if v.get("subrubro"))

    # 2. Encontrar clientes similares
    clientes_similares = obtener_clientes_similares(cuit_objetivo)

    if not clientes_similares:
        return []

    # 3. Calcular matriz de co-ocurrencia
    matriz = calcular_matriz_coocurrencia(clientes_similares)

    if matriz.empty:
        return []

    # 4. Identificar subrubros que el cliente NO tiene pero co-ocurren con los que sí tiene
    oportunidades = []

    for subrubro_tiene in subrubros_cliente:
        if subrubro_tiene not in matriz.index:
            continue

        # Obtener co-ocurrencias con subrubros que el cliente NO tiene
        coocurrencias = matriz.loc[subrubro_tiene]
        for subrubro_oportunidad, count in coocurrencias.items():
            if (subrubro_oportunidad not in subrubros_cliente and
                count >= min_coocurrencia):
                oportunidades.append({
                    "familia": subrubro_oportunidad,
                    "razon": f"Clientes similares que compran {subrubro_tiene} también compran esto",
                    "score": float(count),
                    "coocurrencia": int(count)
                })

    # 5. Agrupar por familia, sumar scores y ordenar
    if not oportunidades:
        return []

    df_oportunidades = pd.DataFrame(oportunidades)
    df_agrupado = df_oportunidades.groupby("familia").agg({
        "score": "sum",
        "coocurrencia": "max",
        "razon": "first"
    }).reset_index()

    df_agrupado = df_agrupado.sort_values("score", ascending=False).head(top_familias)

    return df_agrupado.to_dict("records")


def estimar_potencial_familia(
    familia: str,
    clientes_similares: List[str]
) -> float:
    """
    Estima el potencial de facturación mensual para una familia
    basado en el promedio de clientes similares

    Args:
        familia: Nombre de la familia/subrubro
        clientes_similares: Lista de CUITs de clientes similares

    Returns:
        Potencial mensual estimado en pesos
    """
    if not clientes_similares:
        return 0.0

    supabase = get_supabase()
    fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # Obtener ventas de esta familia para clientes similares
    response = supabase.table("ventas") \
        .select("cuit, monto") \
        .eq("subrubro", familia) \
        .in_("cuit", clientes_similares) \
        .gte("fecha", fecha_12_meses) \
        .in_("empresa", EMPRESAS_GRUPO) \
        .execute()

    if not response.data:
        return 100000.0  # Default si no hay datos

    df = pd.DataFrame(response.data)
    facturacion_total = df["monto"].sum()
    cantidad_clientes = df["cuit"].nunique()

    if cantidad_clientes == 0:
        return 100000.0

    # Promedio anual por cliente / 12 para mensual
    promedio_anual = facturacion_total / cantidad_clientes
    return promedio_anual / 12
