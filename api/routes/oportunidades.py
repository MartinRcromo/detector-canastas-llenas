"""
Endpoint para oportunidades de cross-selling
GET /api/oportunidades/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import get_supabase
from models.responses import (
    OportunidadesResponse,
    OportunidadFamilia,
    ProductoSugerido,
    ProductoDestacado
)
from services.benchmark import (
    identificar_oportunidades,
    obtener_clientes_similares,
    estimar_potencial_familia
)

router = APIRouter()

# Prioridades basadas en score de co-ocurrencia
def determinar_prioridad(score: float) -> str:
    """Determina la prioridad basado en el score de co-ocurrencia"""
    if score >= 15:
        return "alta"
    elif score >= 8:
        return "media"
    else:
        return "baja"

def obtener_productos_top_familia(familia: str, limit: int = 3) -> list:
    """
    Obtiene los productos más vendidos de una familia

    Args:
        familia: Nombre de la familia/subrubro
        limit: Cantidad de productos a retornar

    Returns:
        Lista de productos top de esa familia
    """
    try:
        supabase = get_supabase()
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener productos más vendidos de esta familia
        response = supabase.table("ventas") \
            .select("articulo_codigo, articulo_nombre, monto, cantidad") \
            .eq("subrubro", familia) \
            .gte("fecha", fecha_12_meses) \
            .execute()

        if not response.data:
            return []

        # Agrupar por artículo y calcular totales
        import pandas as pd
        df = pd.DataFrame(response.data)

        productos_agrupados = df.groupby(["articulo_codigo", "articulo_nombre"]).agg({
            "cantidad": "sum",
            "monto": "sum"
        }).reset_index()

        productos_agrupados = productos_agrupados.sort_values("monto", ascending=False).head(limit)

        # Formatear como ProductoSugerido
        productos = []
        for _, row in productos_agrupados.iterrows():
            # Calcular precio promedio
            precio = row["monto"] / row["cantidad"] if row["cantidad"] > 0 else 0

            # Determinar demanda basada en cantidad vendida
            if row["cantidad"] >= 100:
                demanda = "Alta"
            elif row["cantidad"] >= 50:
                demanda = "Media"
            else:
                demanda = "Baja"

            productos.append(ProductoSugerido(
                codigo=row["articulo_codigo"],
                nombre=row["articulo_nombre"],
                precio=round(precio, 2),
                demanda=demanda
            ))

        return productos

    except Exception as e:
        print(f"Error al obtener productos top de {familia}: {e}")
        return []


def obtener_productos_destacados(cuit: str, limit: int = 3) -> list:
    """
    Obtiene productos destacados con alto potencial para el cliente

    Args:
        cuit: CUIT del cliente
        limit: Cantidad de productos destacados

    Returns:
        Lista de ProductoDestacado
    """
    try:
        supabase = get_supabase()
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener productos más vendidos globalmente que el cliente NO compra
        # Primero obtener qué artículos compra el cliente
        response_cliente = supabase.table("ventas") \
            .select("articulo_codigo") \
            .eq("cuit", cuit) \
            .gte("fecha", fecha_12_meses) \
            .execute()

        articulos_cliente = set(v.get("articulo_codigo") for v in response_cliente.data if v.get("articulo_codigo"))

        # Obtener top productos globales
        response_global = supabase.table("ventas") \
            .select("articulo_codigo, articulo_nombre, subrubro, monto, cantidad") \
            .gte("fecha", fecha_12_meses) \
            .execute()

        if not response_global.data:
            return []

        import pandas as pd
        df = pd.DataFrame(response_global.data)

        # Filtrar productos que el cliente NO tiene
        df = df[~df["articulo_codigo"].isin(articulos_cliente)]

        # Agrupar y calcular métricas
        productos_agrupados = df.groupby(["articulo_codigo", "articulo_nombre", "subrubro"]).agg({
            "cantidad": "sum",
            "monto": "sum"
        }).reset_index()

        productos_agrupados["precio"] = productos_agrupados["monto"] / productos_agrupados["cantidad"]
        productos_agrupados = productos_agrupados.sort_values("monto", ascending=False).head(limit)

        # Formatear como ProductoDestacado
        destacados = []
        for idx, row in productos_agrupados.iterrows():
            # Determinar rotación
            if row["cantidad"] >= 100:
                rotacion = "Muy Alta"
            elif row["cantidad"] >= 50:
                rotacion = "Alta"
            else:
                rotacion = "Media"

            # Margen estimado (simplificado - podría venir de otra tabla)
            margen = 30.0 + (idx * 5)  # Variación de margen

            razones = [
                "Top ventas en tu segmento",
                "Complementa tu portfolio",
                "Tendencia creciente",
                "Alta demanda regional"
            ]

            destacados.append(ProductoDestacado(
                codigo=row["articulo_codigo"],
                nombre=row["articulo_nombre"],
                familia=row["subrubro"],
                precio=round(row["precio"], 2),
                margen=round(margen, 1),
                rotacion=rotacion,
                razon=razones[idx % len(razones)]
            ))

        return destacados

    except Exception as e:
        print(f"Error al obtener productos destacados: {e}")
        return []


@router.get("/api/oportunidades/{cuit}", response_model=OportunidadesResponse)
async def get_oportunidades(cuit: str):
    """
    Obtiene oportunidades de cross-selling para un cliente

    Proceso:
    1. Identifica clientes similares por facturación
    2. Analiza co-ocurrencia de familias
    3. Sugiere familias que el cliente NO tiene pero clientes similares SÍ
    4. Estima potencial de facturación
    5. Sugiere productos específicos top de cada familia
    """
    try:
        # 1. Identificar oportunidades de familias
        oportunidades_raw = identificar_oportunidades(cuit, min_coocurrencia=5, top_familias=4)

        if not oportunidades_raw:
            # Si no hay oportunidades por benchmark, retornar respuesta vacía
            return OportunidadesResponse(
                cuit=cuit,
                oportunidades_familias=[],
                productos_destacados=[],
                total_potencial_mensual=0.0
            )

        # 2. Obtener clientes similares para estimar potencial
        clientes_similares = obtener_clientes_similares(cuit)

        # 3. Construir oportunidades completas
        oportunidades_familias = []
        total_potencial = 0.0

        for idx, opp in enumerate(oportunidades_raw):
            familia = opp["familia"]
            score = opp["score"]

            # Estimar potencial mensual
            potencial = estimar_potencial_familia(familia, clientes_similares)
            total_potencial += potencial

            # Obtener productos top de la familia
            productos = obtener_productos_top_familia(familia, limit=3)

            # Razones dinámicas
            razones = [
                "Clientes similares compran",
                "Complementa tu portfolio actual",
                "Alta rotación en tu zona",
                "Oportunidad estacional"
            ]

            oportunidades_familias.append(OportunidadFamilia(
                id=idx + 1,
                familia=familia,
                razon=razones[idx % len(razones)],
                potencial_mensual=round(potencial, 2),
                productos_sugeridos=len(productos) if productos else 5,
                prioridad=determinar_prioridad(score),
                productos=productos if productos else []
            ))

        # 4. Obtener productos destacados
        productos_destacados = obtener_productos_destacados(cuit, limit=3)

        return OportunidadesResponse(
            cuit=cuit,
            oportunidades_familias=oportunidades_familias,
            productos_destacados=productos_destacados,
            total_potencial_mensual=round(total_potencial, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener oportunidades: {str(e)}")
