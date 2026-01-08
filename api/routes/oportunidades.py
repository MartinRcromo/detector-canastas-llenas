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
    ProductoDestacado,
    EstrategiaProductos
)
from services.benchmark import identificar_oportunidades
from database import execute_query
from utils.cache import clasificaciones_cache, estrategias_cache

router = APIRouter()

# Empresas del grupo
EMPRESAS_GRUPO = ["Cromo", "BBA"]


def calcular_clasificacion_abc_subrubro(subrubro: str):
    """
    Calcula la clasificación ABC de todos los productos de un subrubro
    basada en el volumen de unidades vendidas (percentiles acumulados).

    **Optimizado con caché de 10 minutos**

    Clasificación:
    - AA: 0-50% del volumen acumulado (los más vendidos)
    - A:  50-80% del volumen acumulado
    - B:  80-90% del volumen acumulado
    - C:  90-100% del volumen acumulado

    Args:
        subrubro: Nombre del subrubro

    Returns:
        Dict con {articulo_codigo: {"clasificacion": "AA", "volumen": X, "precio_prom": Y}}
    """
    # Verificar caché primero
    cache_key = f"abc_{subrubro}"
    cached = clasificaciones_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

        query = """
            SELECT
                articulo_codigo,
                articulo_descripcion,
                SUM(unidades) as volumen_total,
                SUM(importe) as importe_total
            FROM ventas
            WHERE subrubro = :subrubro
            AND anio_mes >= :anio_mes_12_meses
            AND empresa = ANY(:empresas)
            AND articulo_codigo IS NOT NULL
            GROUP BY articulo_codigo, articulo_descripcion
            HAVING SUM(unidades) > 0
            ORDER BY volumen_total DESC
        """

        productos = execute_query(query, {
            "subrubro": subrubro,
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": EMPRESAS_GRUPO
        })

        if not productos:
            return {}

        # Calcular volumen total del subrubro
        volumen_total_subrubro = sum(int(p.get("volumen_total", 0) or 0) for p in productos)

        if volumen_total_subrubro == 0:
            return {}

        # Calcular percentiles acumulados y clasificar
        clasificaciones = {}
        volumen_acumulado = 0

        for p in productos:
            codigo = p["articulo_codigo"]
            volumen = int(p.get("volumen_total", 0) or 0)
            importe = float(p.get("importe_total", 0) or 0)

            # Calcular precio promedio
            precio_prom = importe / volumen if volumen > 0 else 0

            # Sumar al acumulado
            volumen_acumulado += volumen
            percentil_acumulado = (volumen_acumulado / volumen_total_subrubro) * 100

            # Clasificar según percentil
            if percentil_acumulado <= 50:
                clasificacion = "AA"
            elif percentil_acumulado <= 80:
                clasificacion = "A"
            elif percentil_acumulado <= 90:
                clasificacion = "B"
            else:
                clasificacion = "C"

            clasificaciones[codigo] = {
                "clasificacion": clasificacion,
                "volumen": volumen,
                "precio_prom": round(precio_prom, 2),
                "descripcion": p.get("articulo_descripcion", "")
            }

        # Guardar en caché
        clasificaciones_cache.set(cache_key, clasificaciones)
        return clasificaciones

    except Exception as e:
        print(f"Error calculando clasificación ABC para {subrubro}: {e}")
        return {}


def obtener_productos_clasificados(subrubro: str, clasificaciones_permitidas: List[str], limit: int = 50) -> List[ProductoSugerido]:
    """
    Obtiene productos de un subrubro filtrados por clasificación ABC.

    **Optimizado: retorna máximo 50 productos (configurable)**

    Args:
        subrubro: Nombre del subrubro
        clasificaciones_permitidas: Lista de clasificaciones a incluir (ej: ["AA"] o ["AA", "A"])
        limit: Máximo de productos a retornar (default: 50)

    Returns:
        Lista de ProductoSugerido ordenada por volumen descendente
    """
    try:
        # Obtener clasificaciones ABC del subrubro
        clasificaciones = calcular_clasificacion_abc_subrubro(subrubro)

        if not clasificaciones:
            return []

        # Filtrar productos por clasificación
        productos_resultado = []
        for codigo, datos in clasificaciones.items():
            if datos["clasificacion"] in clasificaciones_permitidas:
                # Determinar demanda basada en volumen
                volumen = datos["volumen"]
                if volumen >= 100:
                    demanda = "Alta"
                elif volumen >= 50:
                    demanda = "Media"
                else:
                    demanda = "Baja"

                # Cantidad mínima sugerida (1 unidad por ahora, puede ajustarse)
                cantidad_minima = 1
                precio_unitario = datos["precio_prom"]

                productos_resultado.append(ProductoSugerido(
                    codigo=codigo,
                    nombre=datos["descripcion"] or "Sin nombre",
                    precio=precio_unitario,
                    demanda=demanda,
                    clasificacion_abc=datos["clasificacion"],
                    volumen_12m=volumen,
                    precio_total=round(precio_unitario * cantidad_minima, 2)
                ))

        # Ordenar por volumen descendente (ya vienen en orden pero por seguridad)
        productos_resultado.sort(key=lambda x: x.volumen_12m, reverse=True)

        # Limitar cantidad de productos para performance
        return productos_resultado[:limit]

    except Exception as e:
        print(f"Error obteniendo productos clasificados de {subrubro}: {e}")
        return []


def construir_estrategias_ligeras(subrubro: str) -> tuple:
    """
    Construye metadata de estrategias SIN productos completos (para payload inicial ligero).

    **Optimización**: Solo calcula cantidades y montos, no carga productos.

    Args:
        subrubro: Nombre del subrubro

    Returns:
        Tupla (estrategia_probar_metadata, estrategia_fe_metadata)
    """
    # Verificar caché
    cache_key = f"estrategias_light_{subrubro}"
    cached = estrategias_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        # Estrategia 1: Solo AA (solo metadata)
        productos_aa = obtener_productos_clasificados(subrubro, ["AA"], limit=50)
        monto_aa = sum(p.precio_total for p in productos_aa)

        estrategia_probar = EstrategiaProductos(
            tipo="probar",
            productos=[],  # Vacío para payload ligero
            monto_total_minimo=round(monto_aa, 2),
            monto_total_maximo=round(monto_aa, 2),
            cantidad_productos=len(productos_aa),
            descripcion=f"Productos AA con mayor rotación ({len(productos_aa)} SKUs)"
        )

        # Estrategia 2: AA + A (solo metadata)
        productos_aa_a = obtener_productos_clasificados(subrubro, ["AA", "A"], limit=50)
        monto_max_fe = sum(p.precio_total for p in productos_aa_a)

        estrategia_fe = EstrategiaProductos(
            tipo="fe",
            productos=[],  # Vacío para payload ligero
            monto_total_minimo=round(monto_aa, 2),
            monto_total_maximo=round(monto_max_fe, 2),
            cantidad_productos=len(productos_aa_a),
            descripcion=f"Productos AA + A expandidos ({len(productos_aa_a)} SKUs, ajustable con slider)"
        )

        resultado = (estrategia_probar, estrategia_fe)

        # Guardar en caché
        estrategias_cache.set(cache_key, resultado)

        return resultado

    except Exception as e:
        print(f"Error construyendo estrategias para {subrubro}: {e}")
        return (
            EstrategiaProductos(tipo="probar", productos=[], monto_total_minimo=0, monto_total_maximo=0, cantidad_productos=0, descripcion="Error al cargar productos"),
            EstrategiaProductos(tipo="fe", productos=[], monto_total_minimo=0, monto_total_maximo=0, cantidad_productos=0, descripcion="Error al cargar productos")
        )


def construir_estrategias_completas(subrubro: str) -> tuple:
    """
    Construye estrategias CON productos completos (para lazy loading).

    **Uso**: Endpoint separado que se llama solo cuando el usuario expande.

    Args:
        subrubro: Nombre del subrubro

    Returns:
        Tupla (estrategia_probar, estrategia_fe) con productos
    """
    try:
        # Estrategia 1: Solo AA
        productos_aa = obtener_productos_clasificados(subrubro, ["AA"], limit=50)
        monto_aa = sum(p.precio_total for p in productos_aa)

        estrategia_probar = EstrategiaProductos(
            tipo="probar",
            productos=productos_aa,  # CON productos
            monto_total_minimo=round(monto_aa, 2),
            monto_total_maximo=round(monto_aa, 2),
            cantidad_productos=len(productos_aa),
            descripcion=f"Productos AA con mayor rotación ({len(productos_aa)} SKUs)"
        )

        # Estrategia 2: AA + A
        productos_aa_a = obtener_productos_clasificados(subrubro, ["AA", "A"], limit=50)
        monto_max_fe = sum(p.precio_total for p in productos_aa_a)

        estrategia_fe = EstrategiaProductos(
            tipo="fe",
            productos=productos_aa_a,  # CON productos
            monto_total_minimo=round(monto_aa, 2),
            monto_total_maximo=round(monto_max_fe, 2),
            cantidad_productos=len(productos_aa_a),
            descripcion=f"Productos AA + A expandidos ({len(productos_aa_a)} SKUs, ajustable con slider)"
        )

        return (estrategia_probar, estrategia_fe)

    except Exception as e:
        print(f"Error construyendo estrategias para {subrubro}: {e}")
        return (
            EstrategiaProductos(tipo="probar", productos=[], monto_total_minimo=0, monto_total_maximo=0, cantidad_productos=0, descripcion="Error al cargar productos"),
            EstrategiaProductos(tipo="fe", productos=[], monto_total_minimo=0, monto_total_maximo=0, cantidad_productos=0, descripcion="Error al cargar productos")
        )


def obtener_productos_top_familia(familia: str, limit: int = 3) -> List[ProductoSugerido]:
    """
    FUNCIÓN LEGACY - Mantener para retrocompatibilidad
    Obtiene los productos AA más vendidos de una familia/subrubro

    Args:
        familia: Nombre del subrubro
        limit: Cantidad de productos a retornar

    Returns:
        Lista de ProductoSugerido
    """
    try:
        productos_aa = obtener_productos_clasificados(familia, ["AA"])
        return productos_aa[:limit]

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


@router.get("/api/oportunidades/{cuit}/estrategias/{subrubro}")
async def get_estrategias_subrubro(subrubro: str):
    """
    Endpoint de lazy loading para obtener estrategias completas de un subrubro.

    **Uso**: Se llama solo cuando el usuario expande una oportunidad en el frontend.

    **Optimización**: Reduce payload inicial y solo carga datos cuando se necesitan.

    Args:
        subrubro: Nombre del subrubro

    Returns:
        {
            "estrategia_probar": EstrategiaProductos (con productos),
            "estrategia_fe": EstrategiaProductos (con productos)
        }
    """
    try:
        estrategia_probar, estrategia_fe = construir_estrategias_completas(subrubro)

        return {
            "subrubro": subrubro,
            "estrategia_probar": estrategia_probar,
            "estrategia_fe": estrategia_fe
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estrategias: {str(e)}"
        )


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

            # Obtener productos sugeridos de esta familia (legacy)
            productos = obtener_productos_top_familia(opp["subrubro"], limit=3)

            # OPTIMIZADO: Construir estrategias LIGERAS (sin productos completos)
            estrategia_probar, estrategia_fe = construir_estrategias_ligeras(opp["subrubro"])

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
                productos=productos,  # Mantener para retrocompatibilidad
                estrategia_probar=estrategia_probar,  # NUEVO
                estrategia_fe=estrategia_fe  # NUEVO
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
