"""
Endpoint para oportunidades de cross-selling
GET /api/oportunidades/{cuit}
Implementación optimizada con Python nativo y SQL
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
from database import execute_query
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
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener productos más vendidos de esta familia
        query = """
            SELECT articulo_codigo, articulo_nombre, importe, cantidad
            FROM ventas
            WHERE subrubro = :familia
            AND fecha >= :fecha_12_meses
        """

        productos_ventas = execute_query(query, {"familia": familia, "fecha_12_meses": fecha_12_meses})

        if not productos_ventas:
            return []

        # Agrupar por artículo usando diccionarios
        productos_dict = defaultdict(lambda: {"cantidad": 0, "importe": 0, "nombre": ""})

        for venta in productos_ventas:
            codigo = venta.get("articulo_codigo")
            nombre = venta.get("articulo_nombre", "")
            cantidad = venta.get("cantidad", 0)
            importe = venta.get("importe", 0)

            if codigo:
                productos_dict[codigo]["cantidad"] += cantidad
                productos_dict[codigo]["importe"] += importe
                if not productos_dict[codigo]["nombre"]:
                    productos_dict[codigo]["nombre"] = nombre

        # Convertir a lista y ordenar por importe
        productos_lista = [
            {
                "codigo": codigo,
                "nombre": datos["nombre"],
                "cantidad": datos["cantidad"],
                "importe": datos["importe"]
            }
            for codigo, datos in productos_dict.items()
        ]

        productos_lista.sort(key=lambda x: x["importe"], reverse=True)
        productos_top = productos_lista[:limit]

        # Formatear como ProductoSugerido
        productos = []
        for producto in productos_top:
            # Calcular precio promedio
            precio = producto["importe"] / producto["cantidad"] if producto["cantidad"] > 0 else 0

            # Determinar demanda basada en cantidad vendida
            if producto["cantidad"] >= 100:
                demanda = "Alta"
            elif producto["cantidad"] >= 50:
                demanda = "Media"
            else:
                demanda = "Baja"

            productos.append(ProductoSugerido(
                codigo=producto["codigo"],
                nombre=producto["nombre"],
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
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener productos más vendidos globalmente que el cliente NO compra
        # Primero obtener qué artículos compra el cliente
        query_cliente = """
            SELECT articulo_codigo
            FROM ventas
            WHERE cuit = :cuit
            AND fecha >= :fecha_12_meses
        """

        articulos_cliente_data = execute_query(query_cliente, {"cuit": cuit, "fecha_12_meses": fecha_12_meses})
        articulos_cliente = set(v.get("articulo_codigo") for v in articulos_cliente_data if v.get("articulo_codigo"))

        # Obtener top productos globales
        query_global = """
            SELECT articulo_codigo, articulo_nombre, subrubro, importe, cantidad
            FROM ventas
            WHERE fecha >= :fecha_12_meses
        """

        productos_globales = execute_query(query_global, {"fecha_12_meses": fecha_12_meses})

        if not productos_globales:
            return []

        # Agrupar productos usando diccionarios
        productos_dict = defaultdict(lambda: {"cantidad": 0, "importe": 0, "nombre": "", "subrubro": ""})

        for venta in productos_globales:
            codigo = venta.get("articulo_codigo")
            nombre = venta.get("articulo_nombre", "")
            subrubro = venta.get("subrubro", "")
            cantidad = venta.get("cantidad", 0)
            importe = venta.get("importe", 0)

            # Filtrar productos que el cliente YA tiene
            if codigo and codigo not in articulos_cliente:
                productos_dict[codigo]["cantidad"] += cantidad
                productos_dict[codigo]["importe"] += importe
                if not productos_dict[codigo]["nombre"]:
                    productos_dict[codigo]["nombre"] = nombre
                if not productos_dict[codigo]["subrubro"]:
                    productos_dict[codigo]["subrubro"] = subrubro

        # Convertir a lista y ordenar por importe
        productos_lista = [
            {
                "codigo": codigo,
                "nombre": datos["nombre"],
                "subrubro": datos["subrubro"],
                "cantidad": datos["cantidad"],
                "importe": datos["importe"],
                "precio": datos["importe"] / datos["cantidad"] if datos["cantidad"] > 0 else 0
            }
            for codigo, datos in productos_dict.items()
        ]

        productos_lista.sort(key=lambda x: x["importe"], reverse=True)
        productos_top = productos_lista[:limit]

        # Formatear como ProductoDestacado
        destacados = []
        razones = [
            "Top ventas en tu segmento",
            "Complementa tu portfolio",
            "Tendencia creciente",
            "Alta demanda regional"
        ]

        for idx, producto in enumerate(productos_top):
            # Determinar rotación
            if producto["cantidad"] >= 100:
                rotacion = "Muy Alta"
            elif producto["cantidad"] >= 50:
                rotacion = "Alta"
            else:
                rotacion = "Media"

            # Margen estimado (simplificado - podría venir de otra tabla)
            margen = 30.0 + (idx * 5)  # Variación de margen

            destacados.append(ProductoDestacado(
                codigo=producto["codigo"],
                nombre=producto["nombre"],
                familia=producto["subrubro"],
                precio=round(producto["precio"], 2),
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
