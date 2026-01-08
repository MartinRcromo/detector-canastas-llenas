"""
Servicio de Brand Affinity para filtrado de recomendaciones
Basado en la metodología de Antigravity
"""
from datetime import datetime, timedelta
from typing import List, Set, Optional
from database import execute_query


def calcular_brand_affinity(
    cuit: str,
    threshold: float = 0.10,
    empresas: List[str] = None
) -> Set[str]:
    """
    Identifica las marcas de vehículos dominantes del cliente.

    Proceso (basado en Antigravity):
    1. Obtiene todas las compras del cliente por marca_vehiculo
    2. Calcula el % de participación de cada marca sobre el total
    3. Retorna marcas que representan >= threshold (default 10%)

    Args:
        cuit: CUIT del cliente
        threshold: % mínimo para considerar marca dominante (0.10 = 10%)
        empresas: Lista de empresas a filtrar (default: todas)

    Returns:
        Set de marcas dominantes (ej: {'FORD', 'CHEVROLET'})
        Si no hay marcas dominantes o no existe el campo, retorna set vacío

    Ejemplo:
        - Cliente compra 60% Ford, 25% Chevrolet, 15% otras
        - threshold = 0.10
        - Retorna: {'FORD', 'CHEVROLET'}
    """
    if empresas is None:
        from routes.oportunidades import EMPRESAS_GRUPO
        empresas = EMPRESAS_GRUPO

    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    try:
        # Intentar obtener compras por marca_vehiculo
        query = """
            SELECT
                UPPER(TRIM(marca_vehiculo)) as marca,
                SUM(importe) as total_importe
            FROM ventas
            WHERE cuit = :cuit
            AND anio_mes >= :anio_mes_12_meses
            AND empresa = ANY(:empresas)
            AND marca_vehiculo IS NOT NULL
            AND marca_vehiculo != ''
            GROUP BY UPPER(TRIM(marca_vehiculo))
        """

        result = execute_query(query, {
            "cuit": cuit,
            "anio_mes_12_meses": anio_mes_12_meses,
            "empresas": empresas
        })

        if not result:
            # No hay datos de marca_vehiculo, retornar set vacío (no filtrar)
            return set()

        # Calcular total general
        total_importe = sum(float(r.get("total_importe", 0) or 0) for r in result)

        if total_importe == 0:
            return set()

        # Identificar marcas dominantes (>= threshold)
        marcas_dominantes = set()

        for row in result:
            marca = row.get("marca")
            importe = float(row.get("total_importe", 0) or 0)
            share = importe / total_importe

            if share >= threshold and marca:
                marcas_dominantes.add(marca)

        return marcas_dominantes

    except Exception as e:
        # Si hay algún error (ej: columna marca_vehiculo no existe),
        # retornar set vacío para no romper el flujo
        print(f"[Brand Affinity] No se pudo calcular para {cuit}: {e}")
        return set()


def filtrar_productos_por_marca(
    productos: List,
    marcas_permitidas: Set[str]
) -> List:
    """
    Filtra productos basándose en marcas permitidas.

    Reglas:
    1. Si marcas_permitidas está vacío, NO filtrar (retornar todos)
    2. Si producto tiene marca_vehiculo:
       - Incluir si marca está en marcas_permitidas
       - Incluir si marca es "UNIVERSAL" o "SIN MARCA"
       - Excluir si marca no está en marcas_permitidas
    3. Si producto NO tiene marca_vehiculo, incluirlo (asumir universal)

    Args:
        productos: Lista de productos (dicts con posible campo 'marca_vehiculo')
        marcas_permitidas: Set de marcas dominantes del cliente

    Returns:
        Lista filtrada de productos
    """
    # Si no hay marcas permitidas, no filtrar
    if not marcas_permitidas:
        return productos

    productos_filtrados = []

    for producto in productos:
        # Obtener marca del producto (puede no existir)
        marca_producto = producto.get("marca_vehiculo")

        # Si no tiene marca, incluir (asumir universal)
        if not marca_producto:
            productos_filtrados.append(producto)
            continue

        # Normalizar marca
        marca_producto = str(marca_producto).upper().strip()

        # Incluir si es universal o sin marca
        if marca_producto in ["UNIVERSAL", "SIN MARCA", "GENERICO", "TODOS"]:
            productos_filtrados.append(producto)
            continue

        # Incluir si está en marcas permitidas
        if marca_producto in marcas_permitidas:
            productos_filtrados.append(producto)
            continue

        # Excluir producto (marca no permitida)

    return productos_filtrados
