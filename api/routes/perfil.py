"""
Endpoint para el perfil del cliente
GET /api/perfil/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import execute_query
from models.responses import PerfilResponse, CompraReciente

router = APIRouter()

def clasificar_cliente(facturacion_anual: float) -> str:
    """
    Clasifica al cliente según su facturación anual
    """
    if facturacion_anual >= 3_000_000:
        return "Activo Plus"
    elif facturacion_anual >= 1_500_000:
        return "Activo"
    elif facturacion_anual >= 500_000:
        return "En desarrollo"
    else:
        return "Nuevo"

@router.get("/api/perfil/{cuit}", response_model=PerfilResponse)
async def get_perfil(cuit: str):
    """
    Obtiene el perfil completo de un cliente por CUIT

    Calcula:
    - Facturación anual (últimos 12 meses)
    - Unidades compradas
    - Cantidad de pedidos
    - Subrubros activos
    - Compras recientes (últimos 10 registros)
    """
    try:
        # Calcular fecha de hace 12 meses
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener todas las ventas del cliente en los últimos 12 meses
        query = """
            SELECT * FROM ventas
            WHERE cuit = :cuit
            AND fecha >= :fecha_12_meses
            ORDER BY fecha DESC
        """

        ventas = execute_query(query, {"cuit": cuit, "fecha_12_meses": fecha_12_meses})

        if not ventas:
            raise HTTPException(status_code=404, detail=f"No se encontraron datos para el CUIT {cuit}")

        # Obtener nombre de empresa del primer registro
        nombre_empresa = ventas[0].get("cliente", "Cliente sin nombre")

        # Calcular métricas agregadas
        facturacion_anual = sum(v.get("importe", 0) for v in ventas)
        unidades_compradas = sum(v.get("cantidad", 0) for v in ventas)

        # Contar pedidos únicos (por fecha + empresa)
        pedidos_unicos = len(set(f"{v.get('fecha')}_{v.get('empresa')}" for v in ventas))

        # Contar subrubros únicos
        subrubros_activos = len(set(v.get("subrubro") for v in ventas if v.get("subrubro")))

        # Clasificar cliente
        clasificacion = clasificar_cliente(facturacion_anual)

        # Preparar compras recientes (últimas 10)
        compras_recientes = []
        for venta in ventas[:10]:
            compras_recientes.append(CompraReciente(
                fecha=venta.get("fecha", ""),
                codigo_articulo=venta.get("articulo_codigo", ""),
                nombre_articulo=venta.get("articulo_nombre", "Producto sin nombre"),
                cantidad=venta.get("cantidad", 0),
                monto=venta.get("importe", 0.0),
                subrubro=venta.get("subrubro", "Sin clasificar")
            ))

        return PerfilResponse(
            cuit=cuit,
            nombre_empresa=nombre_empresa,
            clasificacion=clasificacion,
            facturacion_anual=facturacion_anual,
            unidades_compradas=unidades_compradas,
            cantidad_pedidos=pedidos_unicos,
            subrubros_activos=subrubros_activos,
            compras_recientes=compras_recientes
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {str(e)}")
