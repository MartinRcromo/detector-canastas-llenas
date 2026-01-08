"""
Script para calcular y poblar la tabla cliente_cluster_v2
Implementa la metodología Benchmark de Antigravity
"""
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Agregar el directorio api al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from database import execute_query, engine
from sqlalchemy import text

# Empresas del grupo
EMPRESAS_GRUPO = ["Cromo", "BBA"]


def calcular_cluster_mix(ventas_por_rubro: dict, total_facturacion: float) -> str:
    """
    Determina el tipo de cluster basado en concentración de facturación

    - Si >60% facturación en 1 rubro → ESPECIALISTA_PURO
    - Si >40% facturación en 1 rubro → ESPECIALISTA_DOMINANTE
    - Sino → MULTIRRUBRO
    """
    if total_facturacion == 0:
        return "MULTIRRUBRO"

    # Calcular el share máximo
    max_share = max(ventas_por_rubro.values()) / total_facturacion if ventas_por_rubro else 0

    if max_share > 0.60:
        return "ESPECIALISTA_PURO"
    elif max_share > 0.40:
        return "ESPECIALISTA_DOMINANTE"
    else:
        return "MULTIRRUBRO"


def calcular_cluster_especial(ventas_por_rubro: dict) -> str:
    """
    Retorna el rubro con mayor facturación
    """
    if not ventas_por_rubro:
        return "SIN_CLASIFICAR"

    return max(ventas_por_rubro.items(), key=lambda x: x[1])[0]


def calcular_top1_subrubro(ventas_por_subrubro: dict, total_facturacion: float) -> tuple:
    """
    Retorna (subrubro_top, share_porcentaje)
    """
    if not ventas_por_subrubro or total_facturacion == 0:
        return ("SIN_CLASIFICAR", 0.0)

    top_subrubro, top_importe = max(ventas_por_subrubro.items(), key=lambda x: x[1])
    share = (top_importe / total_facturacion) * 100

    return (top_subrubro, round(share, 2))


def obtener_clientes_activos():
    """
    Obtiene todos los clientes con ventas en los últimos 12 meses
    """
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    query = """
        SELECT DISTINCT cuit, cliente, empresa
        FROM ventas
        WHERE anio_mes >= :anio_mes_12_meses
        AND empresa = ANY(:empresas)
        AND cuit IS NOT NULL
        AND cliente IS NOT NULL
        ORDER BY cuit
    """

    return execute_query(query, {
        "anio_mes_12_meses": anio_mes_12_meses,
        "empresas": EMPRESAS_GRUPO
    })


def calcular_cluster_para_cliente(cuit: str, empresa: str):
    """
    Calcula el cluster completo para un cliente
    """
    anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

    # Obtener ventas del cliente
    query = """
        SELECT rubro, subrubro, importe
        FROM ventas
        WHERE cuit = :cuit
        AND empresa = :empresa
        AND anio_mes >= :anio_mes_12_meses
        AND rubro IS NOT NULL
        AND subrubro IS NOT NULL
    """

    ventas = execute_query(query, {
        "cuit": cuit,
        "empresa": empresa,
        "anio_mes_12_meses": anio_mes_12_meses
    })

    if not ventas:
        return None

    # Agrupar por rubro y subrubro
    ventas_por_rubro = defaultdict(float)
    ventas_por_subrubro = defaultdict(float)
    total_facturacion = 0.0

    for venta in ventas:
        importe = float(venta.get("importe", 0) or 0)
        rubro = venta.get("rubro")
        subrubro = venta.get("subrubro")

        ventas_por_rubro[rubro] += importe
        ventas_por_subrubro[subrubro] += importe
        total_facturacion += importe

    # Calcular clusters
    cluster_mix = calcular_cluster_mix(ventas_por_rubro, total_facturacion)
    cluster_especial = calcular_cluster_especial(ventas_por_rubro)
    top1_rubro, top1_share = calcular_top1_subrubro(ventas_por_subrubro, total_facturacion)

    return {
        "cluster_mix": cluster_mix,
        "cluster_especial": cluster_especial,
        "top1_rubro": top1_rubro,
        "top1_share": top1_share
    }


def crear_tabla_si_no_existe():
    """
    Crea la tabla cliente_cluster_v2 si no existe
    """
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cliente_cluster_v2 (
                empresa TEXT NOT NULL,
                cuit TEXT NOT NULL,
                cliente TEXT,
                cluster_mix TEXT,
                cluster_especial TEXT,
                top1_rubro TEXT,
                top1_share NUMERIC,
                fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (empresa, cuit)
            )
        """))
        conn.commit()
        print("✓ Tabla cliente_cluster_v2 verificada/creada")


def limpiar_tabla():
    """
    Limpia la tabla cliente_cluster_v2
    """
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE cliente_cluster_v2"))
        conn.commit()
        print("✓ Tabla cliente_cluster_v2 limpiada")


def insertar_cluster(cliente_data: dict, cluster_data: dict):
    """
    Inserta un registro de cluster en la tabla
    """
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO cliente_cluster_v2
            (empresa, cuit, cliente, cluster_mix, cluster_especial, top1_rubro, top1_share)
            VALUES (:empresa, :cuit, :cliente, :cluster_mix, :cluster_especial, :top1_rubro, :top1_share)
            ON CONFLICT (empresa, cuit)
            DO UPDATE SET
                cliente = EXCLUDED.cliente,
                cluster_mix = EXCLUDED.cluster_mix,
                cluster_especial = EXCLUDED.cluster_especial,
                top1_rubro = EXCLUDED.top1_rubro,
                top1_share = EXCLUDED.top1_share,
                fecha_calculo = CURRENT_TIMESTAMP
        """), {
            "empresa": cliente_data["empresa"],
            "cuit": cliente_data["cuit"],
            "cliente": cliente_data["cliente"],
            "cluster_mix": cluster_data["cluster_mix"],
            "cluster_especial": cluster_data["cluster_especial"],
            "top1_rubro": cluster_data["top1_rubro"],
            "top1_share": cluster_data["top1_share"]
        })
        conn.commit()


def main():
    """
    Proceso principal de cálculo de clusters
    """
    print("=" * 60)
    print("CÁLCULO DE CLUSTERS - Metodología Benchmark")
    print("=" * 60)
    print()

    # 1. Crear tabla si no existe
    print("PASO 1: Verificando tabla cliente_cluster_v2...")
    crear_tabla_si_no_existe()
    print()

    # 2. Limpiar tabla
    print("PASO 2: Limpiando tabla...")
    limpiar_tabla()
    print()

    # 3. Obtener clientes activos
    print("PASO 3: Obteniendo clientes activos (últimos 12 meses)...")
    clientes = obtener_clientes_activos()
    print(f"✓ {len(clientes)} clientes encontrados")
    print()

    # 4. Calcular clusters
    print("PASO 4: Calculando clusters...")
    print()

    total_procesados = 0
    total_exitosos = 0
    total_sin_datos = 0

    for idx, cliente in enumerate(clientes, 1):
        cuit = cliente["cuit"]
        empresa = cliente["empresa"]
        nombre = cliente["cliente"]

        # Calcular cluster
        cluster_data = calcular_cluster_para_cliente(cuit, empresa)

        if cluster_data:
            # Insertar en BD
            insertar_cluster(cliente, cluster_data)
            total_exitosos += 1

            # Mostrar progreso cada 100 clientes
            if idx % 100 == 0:
                print(f"  Procesados: {idx}/{len(clientes)} clientes...")
        else:
            total_sin_datos += 1

        total_procesados += 1

    # 5. Resumen final
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total procesados:     {total_procesados}")
    print(f"Insertados con éxito: {total_exitosos}")
    print(f"Sin datos suficientes: {total_sin_datos}")
    print()

    # Mostrar distribución de clusters
    print("DISTRIBUCIÓN DE CLUSTERS:")
    query_dist = """
        SELECT cluster_mix, COUNT(*) as cantidad
        FROM cliente_cluster_v2
        GROUP BY cluster_mix
        ORDER BY cantidad DESC
    """
    distribucion = execute_query(query_dist)
    for row in distribucion:
        print(f"  - {row['cluster_mix']}: {row['cantidad']} clientes")

    print()
    print("✓ Proceso completado exitosamente")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
