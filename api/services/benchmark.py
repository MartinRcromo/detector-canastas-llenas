"""
Servicio de benchmark para análisis de oportunidades
Implementa la metodología Benchmark de Antigravity
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from database import execute_query
import statistics

# Empresas del grupo para análisis
EMPRESAS_GRUPO = ["Cromo", "BBA"]


def obtener_cluster_cliente(cuit: str) -> Optional[Dict]:
    """
    Lee el cluster de un cliente desde cliente_cluster_v2

    Args:
        cuit: CUIT del cliente

    Returns:
        Dict con cluster_mix, cluster_especial, top1_rubro, top1_share
        None si no existe
    """
    query = """
        SELECT
            cluster_mix,
            cluster_especial,
            top1_rubro,
            top1_share
        FROM cliente_cluster_v2
        WHERE cuit = :cuit
        LIMIT 1
    """

    result = execute_query(query, {"cuit": cuit})

    if not result:
        return None

    cluster = result[0]
    return {
        "cluster_mix": cluster["cluster_mix"],
        "cluster_especial": cluster["cluster_especial"],
        "top1_rubro": cluster["top1_rubro"],
        "top1_share": float(cluster.get("top1_share", 0) or 0)
    }


def calcular_top1_subrubro_real(cuit: str) -> Optional[str]:
    """
    Calcula el top1 subrubro del cliente basado en ventas reales de últimos 12 meses

    Args:
        cuit: CUIT del cliente

    Returns:
        Nombre del subrubro con mayor facturación o None
    """
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    query = """
        SELECT subrubro, SUM(importe) as total
        FROM ventas
        WHERE cuit = :cuit
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
        AND subrubro IS NOT NULL
        GROUP BY subrubro
        ORDER BY total DESC
        LIMIT 1
    """

    result = execute_query(query, {
        "cuit": cuit,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })

    return result[0]["subrubro"] if result else None


def obtener_lideres_benchmark(
    cluster_mix: str,
    cluster_especial: str,
    top1_subrubro: str,
    min_pares: int = 5,
    empresas: List[str] = None
) -> List[str]:
    """
    Identifica los líderes del micro-segmento (Top 25%)

    Proceso:
    1. Busca clientes con mismo perfil (mix + especial + top1)
    2. Si < min_pares, relaja búsqueda (solo mix + especial)
    3. Calcula P75 de facturación del segmento
    4. Retorna CUITs con facturación >= P75

    Args:
        cluster_mix: Tipo de cluster (ESPECIALISTA_PURO, etc.)
        cluster_especial: Rubro principal
        top1_subrubro: Subrubro principal
        min_pares: Mínimo de pares para considerar válido el micro-segmento
        empresas: Lista de empresas a filtrar (default: todas)

    Returns:
        Lista de CUITs de los líderes
    """
    if empresas is None:
        empresas = EMPRESAS_GRUPO

    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # PASO 1: Intentar con criterio estricto (mix + especial + top1)
    query_estricto = """
        WITH clientes_segmento AS (
            SELECT DISTINCT c.cuit
            FROM cliente_cluster_v2 c
            WHERE c.cluster_mix = :cluster_mix
            AND c.cluster_especial = :cluster_especial
            AND c.top1_rubro = :top1_subrubro
        )
        SELECT
            cs.cuit,
            SUM(v.importe) as facturacion_total
        FROM clientes_segmento cs
        JOIN ventas v ON v.cuit = cs.cuit
        WHERE v.anio_mes >= :anio_mes_12_meses
        AND v.empresa = ANY(:empresas)
        GROUP BY cs.cuit
        HAVING SUM(v.importe) > 0
    """

    clientes_segmento = execute_query(query_estricto, {
        "cluster_mix": cluster_mix,
        "cluster_especial": cluster_especial,
        "top1_subrubro": top1_subrubro,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": empresas
    })

    # PASO 2: Si no hay suficientes pares, relajar búsqueda (solo mix + especial)
    if len(clientes_segmento) < min_pares:
        query_relajado = """
            WITH clientes_segmento AS (
                SELECT DISTINCT c.cuit
                FROM cliente_cluster_v2 c
                WHERE c.cluster_mix = :cluster_mix
                AND c.cluster_especial = :cluster_especial
            )
            SELECT
                cs.cuit,
                SUM(v.importe) as facturacion_total
            FROM clientes_segmento cs
            JOIN ventas v ON v.cuit = cs.cuit
            WHERE v.anio_mes >= :anio_mes_12_meses
            AND v.empresa = ANY(:empresas)
            GROUP BY cs.cuit
            HAVING SUM(v.importe) > 0
        """

        clientes_segmento = execute_query(query_relajado, {
            "cluster_mix": cluster_mix,
            "cluster_especial": cluster_especial,
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": empresas
        })

    if not clientes_segmento:
        return []

    # PASO 3: Calcular percentil 75 (P75)
    facturaciones = [float(c["facturacion_total"] or 0) for c in clientes_segmento]

    if not facturaciones:
        return []

    p75 = statistics.quantiles(facturaciones, n=4)[2]  # P75 = cuartil 3

    # PASO 4: Filtrar líderes (facturación >= P75)
    lideres = [
        c["cuit"]
        for c in clientes_segmento
        if float(c["facturacion_total"] or 0) >= p75
    ]

    return lideres


def calcular_canasta_ideal(cuits_lideres: List[str], empresas: List[str] = None) -> Dict[str, float]:
    """
    Calcula la canasta ideal del segmento (Basket Share)

    Proceso:
    1. Suma todas las ventas de los líderes por subrubro
    2. Calcula el % share de cada subrubro sobre el total
    3. Este % representa la "canasta ideal"

    Args:
        cuits_lideres: Lista de CUITs de los líderes
        empresas: Lista de empresas a filtrar (default: todas)

    Returns:
        Dict {subrubro: share_porcentaje}
    """
    if not cuits_lideres:
        return {}

    if empresas is None:
        empresas = EMPRESAS_GRUPO

    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    query = """
        SELECT
            subrubro,
            SUM(importe) as total_subrubro
        FROM ventas
        WHERE cuit = ANY(:cuits)
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
        AND subrubro IS NOT NULL
        GROUP BY subrubro
    """

    ventas_lideres = execute_query(query, {
        "cuits": cuits_lideres,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": empresas
    })

    if not ventas_lideres:
        return {}

    # Calcular total general
    total_general = sum(float(v["total_subrubro"] or 0) for v in ventas_lideres)

    if total_general == 0:
        return {}

    # Calcular share % de cada subrubro
    canasta_ideal = {}
    for venta in ventas_lideres:
        subrubro = venta["subrubro"]
        total_subrubro = float(venta["total_subrubro"] or 0)
        share_porcentaje = (total_subrubro / total_general) * 100
        canasta_ideal[subrubro] = round(share_porcentaje, 2)

    return canasta_ideal


def identificar_oportunidades(
    cuit_objetivo: str,
    min_gap_porcentaje: float = 20.0,
    top_oportunidades: int = 10,
    empresas: List[str] = None
) -> List[Dict]:
    """
    Identifica oportunidades de cross-selling usando metodología Benchmark

    Proceso:
    1. Obtiene cluster del cliente
    2. Identifica líderes del micro-segmento
    3. Calcula canasta ideal de los líderes
    4. Obtiene ventas reales del cliente
    5. Gap Analysis:
       - importe_ideal = venta_total_cliente × (share_ideal / 100)
       - gap = importe_ideal - importe_real
       - gap_% = (gap / importe_ideal) × 100
    6. Filtra oportunidades con gap >= min_gap_porcentaje
    7. Ordena por gap $ descendente

    Args:
        cuit_objetivo: CUIT del cliente
        min_gap_porcentaje: % mínimo de gap para considerar oportunidad
        top_oportunidades: Cantidad máxima de oportunidades a retornar
        empresas: Lista de empresas a filtrar (default: todas)

    Returns:
        Lista de oportunidades con formato:
        {
            "subrubro": str,
            "importe_ideal": float,
            "importe_real": float,
            "gap_importe": float,
            "gap_porcentaje": float,
            "share_ideal": float
        }
    """
    if empresas is None:
        empresas = EMPRESAS_GRUPO

    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # PASO 1: Obtener cluster del cliente
    cluster = obtener_cluster_cliente(cuit_objetivo)

    if not cluster:
        return []

    # PASO 2: Obtener líderes del micro-segmento
    lideres = obtener_lideres_benchmark(
        cluster_mix=cluster["cluster_mix"],
        cluster_especial=cluster["cluster_especial"],
        top1_subrubro=cluster["top1_rubro"],
        empresas=empresas
    )

    if not lideres:
        return []

    # PASO 3: Calcular canasta ideal
    canasta_ideal = calcular_canasta_ideal(lideres, empresas)

    if not canasta_ideal:
        return []

    # PASO 4: Obtener ventas reales del cliente
    query_cliente = """
        SELECT subrubro, SUM(importe) as total
        FROM ventas
        WHERE cuit = :cuit
        AND anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
        AND subrubro IS NOT NULL
        GROUP BY subrubro
    """

    ventas_cliente = execute_query(query_cliente, {
        "cuit": cuit_objetivo,
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": empresas
    })

    # Convertir a dict para lookup rápido
    ventas_reales = {
        v["subrubro"]: float(v["total"] or 0)
        for v in ventas_cliente
    }

    # Calcular facturación total del cliente
    total_cliente = sum(ventas_reales.values())

    if total_cliente == 0:
        return []

    # PASO 5: Gap Analysis
    oportunidades = []

    for subrubro, share_ideal in canasta_ideal.items():
        # Importe ideal = facturación total × (share ideal / 100)
        importe_ideal = total_cliente * (share_ideal / 100)

        # Importe real que tiene actualmente
        importe_real = ventas_reales.get(subrubro, 0.0)

        # Gap
        gap_importe = importe_ideal - importe_real

        # Gap %
        gap_porcentaje = (gap_importe / importe_ideal) * 100 if importe_ideal > 0 else 0

        # PASO 6: Filtrar solo oportunidades significativas
        if gap_importe > 0 and gap_porcentaje >= min_gap_porcentaje:
            oportunidades.append({
                "subrubro": subrubro,
                "importe_ideal": round(importe_ideal, 2),
                "importe_real": round(importe_real, 2),
                "gap_importe": round(gap_importe, 2),
                "gap_porcentaje": round(gap_porcentaje, 2),
                "share_ideal": share_ideal,
                "cantidad_lideres": len(lideres)
            })

    # PASO 7: Ordenar por gap $ descendente y tomar top N
    oportunidades.sort(key=lambda x: x["gap_importe"], reverse=True)

    return oportunidades[:top_oportunidades]
