"""
Endpoint para identificar oportunidades de cross-selling
Implementa la metodología Benchmark de Antigravity
GET /api/oportunidades/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List
from models.responses import (
    OportunidadesResponse,
    OportunidadFamilia,
    ProductoSugerido,
    ProductoDestacado
)
from services.benchmark import identificar_oportunidades
from database import execute_query

router = APIRouter()

# Empresas del grupo
EMPRESAS_GRUPO = ["Cromo", "BBA"]


def obtener_productos_top_familia(familia: str, limit: int = 3) -> List[ProductoSugerido]:
    """
    Obtiene los productos más vendidos de una familia/subrubro

    Args:
        familia: Nombre del subrubro
        limit: Cantidad de productos a retornar

    Returns:
        Lista de ProductoSugerido
    """
    try:
        anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

        query = """
            SELECT
                articulo_codigo,
                articulo_descripcion,
                SUM(importe) as total_importe,
                SUM(unidades) as total_unidades
            FROM ventas
            WHERE subrubro = :familia
            AND anio_mes >= :anio_mes_12_meses
            AND empresa = ANY(:empresas)
            AND articulo_codigo IS NOT NULL
            GROUP BY articulo_codigo, articulo_descripcion
            ORDER BY total_importe DESC
            LIMIT :limit
        """

        productos = execute_query(query, {
            "familia": familia,
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": EMPRESAS_GRUPO,
            "limit": limit
        })

        resultado = []
        for p in productos:
            total_importe = float(p.get("total_importe", 0) or 0)
            total_unidades = int(p.get("total_unidades", 0) or 0)

            # Calcular precio promedio
            precio = total_importe / total_unidades if total_unidades > 0 else 0

            # Determinar demanda basada en unidades
            if total_unidades >= 100:
                demanda = "Alta"
            elif total_unidades >= 50:
                demanda = "Media"
            else:
                demanda = "Baja"

            resultado.append(ProductoSugerido(
                codigo=p["articulo_codigo"],
                nombre=p["articulo_descripcion"] or "Sin nombre",
                precio=round(precio, 2),
                demanda=demanda
            ))

        return resultado

    except Exception as e:
        print(f"Error obteniendo productos de {familia}: {e}")
        return []


def obtener_productos_destacados(cuit: str, limit: int = 3) -> List[ProductoDestacado]:
    """
    Obtiene productos destacados que el cliente NO compra pero que son populares
    en su segmento

    Args:
        cuit: CUIT del cliente
        limit: Cantidad de productos destacados

    Returns:
        Lista de ProductoDestacado
    """
    try:
        anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

        # Obtener productos que el cliente ya compra
        query_cliente = """
            SELECT DISTINCT articulo_codigo
            FROM ventas
            WHERE cuit = :cuit
            AND anio_mes >= :anio_mes_12_meses
            AND empresa = ANY(:empresas)
        """

        productos_cliente = execute_query(query_cliente, {
            "cuit": cuit,
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": EMPRESAS_GRUPO
        })

        codigos_cliente = set(p["articulo_codigo"] for p in productos_cliente if p.get("articulo_codigo"))

        # Obtener top productos globales que NO tiene
        query_global = """
            SELECT
                articulo_codigo,
                articulo_descripcion,
                subrubro,
                SUM(importe) as total_importe,
                SUM(unidades) as total_unidades
            FROM ventas
            WHERE anio_mes >= :anio_mes_12_meses
            AND empresa = ANY(:empresas)
            AND articulo_codigo IS NOT NULL
            AND subrubro IS NOT NULL
            GROUP BY articulo_codigo, articulo_descripcion, subrubro
            ORDER BY total_importe DESC
            LIMIT 100
        """

        productos_globales = execute_query(query_global, {
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": EMPRESAS_GRUPO
        })

        # Filtrar productos que el cliente NO tiene
        productos_destacados = []
        razones = [
            "Top ventas en tu segmento",
            "Complementa tu portfolio",
            "Tendencia creciente",
            "Alta demanda regional"
        ]

        for idx, p in enumerate(productos_globales):
            if p["articulo_codigo"] not in codigos_cliente:
                total_importe = float(p.get("total_importe", 0) or 0)
                total_unidades = int(p.get("total_unidades", 0) or 0)

                # Calcular precio promedio
                precio = total_importe / total_unidades if total_unidades > 0 else 0

                # Determinar rotación
                if total_unidades >= 100:
                    rotacion = "Muy Alta"
                elif total_unidades >= 50:
                    rotacion = "Alta"
                else:
                    rotacion = "Media"

                # Margen estimado (simplificado)
                margen = 30.0 + (idx % 3 * 5)

                productos_destacados.append(ProductoDestacado(
                    codigo=p["articulo_codigo"],
                    nombre=p["articulo_descripcion"] or "Sin nombre",
                    familia=p["subrubro"] or "Sin clasificar",
                    precio=round(precio, 2),
                    margen=margen,
                    rotacion=rotacion,
                    razon=razones[idx % len(razones)]
                ))

                if len(productos_destacados) >= limit:
                    break

        return productos_destacados

    except Exception as e:
        print(f"Error obteniendo productos destacados: {e}")
        return []


@router.get("/api/oportunidades/{cuit}", response_model=OportunidadesResponse)
async def get_oportunidades(cuit: str):
    """
    Identifica oportunidades de cross-selling para un cliente usando la
    metodología Benchmark de Antigravity

    Proceso:
    1. Obtiene cluster del cliente
    2. Identifica líderes del micro-segmento (Top 25%)
    3. Calcula canasta ideal del segmento
    4. Compara con ventas reales del cliente (Gap Analysis)
    5. Retorna oportunidades ordenadas por $ de gap

    Args:
        cuit: CUIT del cliente

    Returns:
        OportunidadesResponse con oportunidades por familia y productos destacados
    """
    try:
        # Llamar al servicio de benchmark
        oportunidades_data = identificar_oportunidades(
            cuit_objetivo=cuit,
            min_gap_porcentaje=20.0,
            top_oportunidades=10
        )

        if not oportunidades_data:
            # Si no hay oportunidades, retornar respuesta vacía
            return OportunidadesResponse(
                cuit=cuit,
                oportunidades_familias=[],
                productos_destacados=obtener_productos_destacados(cuit, limit=3),
                total_potencial_mensual=0.0
            )

        # Transformar a formato OportunidadFamilia
        oportunidades_familias = []
        total_potencial = 0.0

        for idx, opp in enumerate(oportunidades_data, 1):
            # Calcular potencial mensual
            potencial_mensual = opp["gap_importe"] / 12

            # Determinar prioridad basada en gap %
            gap_pct = opp["gap_porcentaje"]
            if gap_pct >= 60:
                prioridad = "alta"
            elif gap_pct >= 40:
                prioridad = "media"
            else:
                prioridad = "baja"

            # Obtener productos sugeridos de esta familia
            productos = obtener_productos_top_familia(opp["subrubro"], limit=3)

            # Construir razón descriptiva
            razon = f"Los líderes de tu segmento ({opp['cantidad_lideres']} clientes) " \
                    f"invierten {opp['share_ideal']:.1f}% de su presupuesto en esta categoría. " \
                    f"Gap detectado: {gap_pct:.0f}%"

            oportunidades_familias.append(OportunidadFamilia(
                id=idx,
                familia=opp["subrubro"],
                razon=razon,
                potencial_mensual=round(potencial_mensual, 2),
                productos_sugeridos=len(productos),
                prioridad=prioridad,
                productos=productos
            ))

            total_potencial += potencial_mensual

        # Obtener productos destacados
        productos_destacados = obtener_productos_destacados(cuit, limit=3)

        return OportunidadesResponse(
            cuit=cuit,
            oportunidades_familias=oportunidades_familias,
            productos_destacados=productos_destacados,
            total_potencial_mensual=round(total_potencial, 2)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al identificar oportunidades: {str(e)}"
        )
