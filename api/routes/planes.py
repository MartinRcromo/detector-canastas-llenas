"""
Endpoint para planes de activación comercial (tiers)
GET /api/planes/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import execute_query
from models.responses import PlanesResponse, Tier
from typing import Optional

router = APIRouter()

# Definición de tiers del programa
TIERS_CONFIG = [
    {
        "nombre": "Bronze",
        "color": "from-orange-100 to-yellow-100",
        "borderColor": "border-orange-300",
        "iconColor": "text-orange-600",
        "rango": "< $1M anual",
        "objetivo": 1_000_000,
        "descuento": "5%",
        "beneficios": [
            "Descuento base 5%",
            "Asesor comercial asignado",
            "Portal de análisis comercial",
            "Acceso a catálogo completo"
        ]
    },
    {
        "nombre": "Silver",
        "color": "from-gray-200 to-gray-300",
        "borderColor": "border-gray-400",
        "iconColor": "text-gray-600",
        "rango": "$1M - $3M anual",
        "objetivo": 3_000_000,
        "descuento": "5-7%",
        "beneficios": [
            "Todo lo de Bronze",
            "Flete promocional (pedidos >$100k)",
            "Alertas de stock crítico",
            "Reportes mensuales personalizados"
        ]
    },
    {
        "nombre": "Gold",
        "color": "from-yellow-200 to-yellow-300",
        "borderColor": "border-yellow-400",
        "iconColor": "text-yellow-600",
        "rango": "$3M - $6M anual",
        "objetivo": 6_000_000,
        "descuento": "7-10%",
        "beneficios": [
            "Todo lo de Silver",
            "Plazo de pago 30 días",
            "Co-marketing digital",
            "Prioridad en atención técnica",
            "Material de marketing personalizado"
        ]
    },
    {
        "nombre": "Platinum",
        "color": "from-purple-200 to-pink-200",
        "borderColor": "border-purple-400",
        "iconColor": "text-purple-600",
        "rango": ">$6M anual",
        "objetivo": 10_000_000,
        "descuento": "10-15%",
        "beneficios": [
            "Todo lo de Gold",
            "Capacitación técnica trimestral",
            "Account Manager exclusivo",
            "Lanzamientos anticipados",
            "Condiciones especiales personalizadas"
        ]
    }
]

def calcular_tier_actual(facturacion_anual: float) -> str:
    """
    Determina el tier actual del cliente basado en su facturación anual

    Args:
        facturacion_anual: Facturación anual del cliente

    Returns:
        Nombre del tier actual
    """
    if facturacion_anual < 1_000_000:
        return "Bronze"
    elif facturacion_anual < 3_000_000:
        return "Silver"
    elif facturacion_anual < 6_000_000:
        return "Gold"
    else:
        return "Platinum"

def obtener_siguiente_tier(tier_actual: str) -> Optional[dict]:
    """
    Obtiene el siguiente tier disponible

    Args:
        tier_actual: Nombre del tier actual

    Returns:
        Configuración del siguiente tier o None si ya está en el máximo
    """
    tier_index = next((i for i, t in enumerate(TIERS_CONFIG) if t["nombre"] == tier_actual), None)

    if tier_index is None or tier_index >= len(TIERS_CONFIG) - 1:
        return None

    return TIERS_CONFIG[tier_index + 1]

@router.get("/api/planes/{cuit}", response_model=PlanesResponse)
async def get_planes(cuit: str):
    """
    Obtiene el plan de activación comercial del cliente

    Calcula:
    - Tier actual basado en facturación anual
    - Progreso hacia el siguiente tier
    - Brecha de facturación para alcanzar el siguiente nivel
    - Beneficios de cada tier
    """
    try:
        # Calcular anio_mes de hace 12 meses
        anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

        # Obtener facturación anual del cliente
        query = """
            SELECT importe FROM ventas
            WHERE cuit = :cuit
            AND anio_mes >= :anio_mes_12_meses
        """

        ventas_data = execute_query(query, {"cuit": cuit, "anio_mes_12_meses": anio_mes_12_meses})

        if not ventas_data:
            # Cliente sin datos - asignar tier Bronze por defecto
            facturacion_anual = 0.0
        else:
            facturacion_anual = sum(v.get("importe", 0) for v in ventas_data)

        # Determinar tier actual
        tier_actual_nombre = calcular_tier_actual(facturacion_anual)

        # Obtener siguiente tier
        siguiente_tier_config = obtener_siguiente_tier(tier_actual_nombre)

        # Calcular brecha y progreso
        if siguiente_tier_config:
            siguiente_tier_nombre = siguiente_tier_config["nombre"]
            objetivo_siguiente = siguiente_tier_config["objetivo"]
            brecha = objetivo_siguiente - facturacion_anual
            porcentaje_progreso = (facturacion_anual / objetivo_siguiente) * 100
        else:
            siguiente_tier_nombre = None
            brecha = None
            porcentaje_progreso = None

        # Construir lista de tiers
        tiers = [
            Tier(
                nombre=t["nombre"],
                color=t["color"],
                borderColor=t["borderColor"],
                iconColor=t["iconColor"],
                rango=t["rango"],
                objetivo=t["objetivo"],
                descuento=t["descuento"],
                beneficios=t["beneficios"]
            )
            for t in TIERS_CONFIG
        ]

        return PlanesResponse(
            cuit=cuit,
            facturacion_anual=round(facturacion_anual, 2),
            tier_actual=tier_actual_nombre,
            tiers=tiers,
            siguiente_tier=siguiente_tier_nombre,
            brecha_siguiente=round(brecha, 2) if brecha is not None else None,
            porcentaje_progreso=round(porcentaje_progreso, 1) if porcentaje_progreso is not None else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener planes: {str(e)}")
