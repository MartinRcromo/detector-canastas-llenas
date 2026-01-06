"""
Servicio de benchmark y análisis de co-ocurrencia
Identifica oportunidades de cross-selling basado en clientes similares
Implementación optimizada con Python nativo y SQL
"""
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from database import execute_query

# Empresas del grupo para análisis
EMPRESAS_GRUPO = ["Cromo", "BBA"]

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
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # Obtener facturación del cliente objetivo
    query_objetivo = """
        SELECT importe FROM ventas
        WHERE cuit = :cuit
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
    """

    ventas_objetivo = execute_query(query_objetivo, {
        "cuit": cuit_objetivo,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })

    if not ventas_objetivo:
        return []

    facturacion_objetivo = sum(v.get("importe", 0) for v in ventas_objetivo)

    # Definir rango de facturación
    if facturacion_min is None:
        facturacion_min = facturacion_objetivo * 0.7
    if facturacion_max is None:
        facturacion_max = facturacion_objetivo * 1.3

    # Obtener todos los clientes y su facturación
    query_todos = """
        SELECT cuit, importe FROM ventas
        WHERE anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
        AND cuit != :cuit_objetivo
    """

    ventas_todos = execute_query(query_todos, {
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO,
        "cuit_objetivo": cuit_objetivo
    })

    if not ventas_todos:
        return []

    # Agrupar por CUIT y calcular facturación usando diccionarios
    facturacion_por_cliente = defaultdict(float)
    for venta in ventas_todos:
        cuit = venta.get("cuit")
        importe = venta.get("importe", 0)
        if cuit:
            facturacion_por_cliente[cuit] += importe

    # Filtrar por rango de facturación
    clientes_en_rango = []
    for cuit, facturacion in facturacion_por_cliente.items():
        if facturacion_min <= facturacion <= facturacion_max:
            diferencia = abs(facturacion - facturacion_objetivo)
            clientes_en_rango.append((cuit, facturacion, diferencia))

    # Ordenar por similitud (menor diferencia primero) y tomar top_n
    clientes_en_rango.sort(key=lambda x: x[2])
    clientes_similares = [cuit for cuit, _, _ in clientes_en_rango[:top_n]]

    return clientes_similares


def calcular_matriz_coocurrencia(cuits: List[str]) -> Dict[str, Dict[str, int]]:
    """
    Calcula la matriz de co-ocurrencia de subrubros para un conjunto de clientes

    Args:
        cuits: Lista de CUITs a analizar

    Returns:
        Diccionario con la matriz de co-ocurrencia (subrubro -> subrubro -> count)
    """
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # Obtener todas las compras de estos clientes
    query = """
        SELECT cuit, subrubro FROM ventas
        WHERE cuit = ANY(:cuits)
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
    """

    ventas_data = execute_query(query, {
        "cuits": cuits,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })

    if not ventas_data:
        return {}

    # Obtener subrubros únicos por cliente
    subrubros_por_cliente = defaultdict(set)
    for venta in ventas_data:
        cuit = venta.get("cuit")
        subrubro = venta.get("subrubro")
        if cuit and subrubro:
            subrubros_por_cliente[cuit].add(subrubro)

    # Calcular co-ocurrencias
    matriz = defaultdict(lambda: defaultdict(int))

    for cuit, subrubros in subrubros_por_cliente.items():
        subrubros_lista = list(subrubros)
        for i, sub1 in enumerate(subrubros_lista):
            for sub2 in subrubros_lista[i+1:]:
                matriz[sub1][sub2] += 1
                matriz[sub2][sub1] += 1

    return dict(matriz)


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
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # 1. Obtener subrubros que el cliente YA compra
    query_cliente = """
        SELECT subrubro FROM ventas
        WHERE cuit = :cuit
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
    """

    subrubros_data = execute_query(query_cliente, {
        "cuit": cuit_objetivo,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })

    if not subrubros_data:
        return []

    subrubros_cliente = set(v.get("subrubro") for v in subrubros_data if v.get("subrubro"))

    # 2. Encontrar clientes similares
    clientes_similares = obtener_clientes_similares(cuit_objetivo)

    if not clientes_similares:
        return []

    # 3. Calcular matriz de co-ocurrencia
    matriz = calcular_matriz_coocurrencia(clientes_similares)

    if not matriz:
        return []

    # 4. Identificar subrubros que el cliente NO tiene pero co-ocurren con los que sí tiene
    oportunidades = []

    for subrubro_tiene in subrubros_cliente:
        if subrubro_tiene not in matriz:
            continue

        # Obtener co-ocurrencias con subrubros que el cliente NO tiene
        coocurrencias = matriz[subrubro_tiene]
        for subrubro_oportunidad, count in coocurrencias.items():
            if subrubro_oportunidad not in subrubros_cliente and count >= min_coocurrencia:
                oportunidades.append({
                    "familia": subrubro_oportunidad,
                    "razon": f"Clientes similares que compran {subrubro_tiene} también compran esto",
                    "score": float(count),
                    "coocurrencia": int(count)
                })

    # 5. Agrupar por familia, sumar scores y ordenar
    if not oportunidades:
        return []

    # Agrupar manualmente por familia
    familias_agrupadas = defaultdict(lambda: {"score": 0, "coocurrencia": 0, "razon": ""})

    for opp in oportunidades:
        familia = opp["familia"]
        familias_agrupadas[familia]["score"] += opp["score"]
        familias_agrupadas[familia]["coocurrencia"] = max(
            familias_agrupadas[familia]["coocurrencia"],
            opp["coocurrencia"]
        )
        if not familias_agrupadas[familia]["razon"]:
            familias_agrupadas[familia]["razon"] = opp["razon"]

    # Convertir a lista y ordenar por score
    resultado = [
        {
            "familia": familia,
            "score": datos["score"],
            "coocurrencia": datos["coocurrencia"],
            "razon": datos["razon"]
        }
        for familia, datos in familias_agrupadas.items()
    ]

    # Ordenar por score descendente y tomar top_familias
    resultado.sort(key=lambda x: x["score"], reverse=True)
    return resultado[:top_familias]


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

    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # Obtener ventas de esta familia para clientes similares
    query = """
        SELECT cuit, importe FROM ventas
        WHERE subrubro = :familia
        AND cuit = ANY(:cuits)
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
    """

    ventas_familia = execute_query(query, {
        "familia": familia,
        "cuits": clientes_similares,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })

    if not ventas_familia:
        return 100000.0  # Default si no hay datos

    # Calcular totales usando diccionarios
    facturacion_total = sum(v.get("importe", 0) for v in ventas_familia)
    cuits_unicos = set(v.get("cuit") for v in ventas_familia if v.get("cuit"))
    cantidad_clientes = len(cuits_unicos)

    if cantidad_clientes == 0:
        return 100000.0

    # Promedio anual por cliente / 12 para mensual
    promedio_anual = facturacion_total / cantidad_clientes
    return promedio_anual / 12
