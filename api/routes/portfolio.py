"""
Endpoint para el portfolio del cliente
GET /api/portfolio/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import get_supabase
from models.responses import PortfolioResponse, FamiliaConfirmada, FamiliaDisponible

router = APIRouter()

# Mapeo de subrubros a familias (basado en la estructura del negocio)
SUBRUBRO_A_FAMILIA = {
    "Filtros": "Filtros",
    "Frenos": "Frenos",
    "Aceites": "Aceites y lubricantes",
    "Lubricantes": "Aceites y lubricantes",
    "Iluminación": "Iluminación",
    "Lámparas": "Iluminación",
    "Suspensión": "Suspensión",
    "Amortiguadores": "Suspensión",
    "Transmisión": "Transmisión",
    "Embrague": "Embrague",
    "Refrigeración": "Refrigeración",
    "Baterías": "Baterías",
    "Escapes": "Escapes",
    "Distribución": "Distribución",
    "Encendido": "Encendido",
    "Eléctrico": "Eléctrico",
    "Limpiaparabrisas": "Limpiaparabrisas",
    "Dirección": "Dirección",
    "Juntas": "Juntas",
    "Retenes": "Retenes",
}

# Todas las familias posibles con iconos
FAMILIAS_TODAS = [
    {"id": 1, "nombre": "Filtros", "icono": "Filter", "subfamilias": "(aire, aceite, combustible)"},
    {"id": 2, "nombre": "Frenos", "icono": "Disc", "subfamilias": "(pastillas, discos, tambores)"},
    {"id": 3, "nombre": "Aceites y lubricantes", "icono": "Droplet", "subfamilias": ""},
    {"id": 4, "nombre": "Iluminación", "icono": "Lightbulb", "subfamilias": "(lámparas, faros)"},
    {"id": 5, "nombre": "Suspensión", "icono": "Activity", "subfamilias": "(amortiguadores, resortes)"},
    {"id": 6, "nombre": "Transmisión", "icono": "Cog", "subfamilias": ""},
    {"id": 7, "nombre": "Embrague", "icono": "CircleDot", "subfamilias": ""},
    {"id": 8, "nombre": "Refrigeración", "icono": "Wind", "subfamilias": ""},
    {"id": 9, "nombre": "Baterías", "icono": "Battery", "subfamilias": ""},
    {"id": 10, "nombre": "Escapes", "icono": "TrendingUp", "subfamilias": ""},
    {"id": 11, "nombre": "Distribución", "icono": "Activity", "subfamilias": ""},
    {"id": 12, "nombre": "Encendido", "icono": "Zap", "subfamilias": ""},
    {"id": 13, "nombre": "Eléctrico", "icono": "Plug", "subfamilias": ""},
    {"id": 14, "nombre": "Limpiaparabrisas", "icono": "Droplets", "subfamilias": ""},
    {"id": 15, "nombre": "Dirección", "icono": "Navigation", "subfamilias": ""},
    {"id": 16, "nombre": "Juntas", "icono": "Circle", "subfamilias": ""},
    {"id": 17, "nombre": "Retenes", "icono": "Disc", "subfamilias": ""},
    {"id": 18, "nombre": "Correas", "icono": "Link", "subfamilias": ""},
    {"id": 19, "nombre": "Rodamientos", "icono": "Disc", "subfamilias": ""},
    {"id": 20, "nombre": "Sistema de escape", "icono": "Wind", "subfamilias": ""},
]

TOTAL_FAMILIAS = len(FAMILIAS_TODAS)

@router.get("/api/portfolio/{cuit}", response_model=PortfolioResponse)
async def get_portfolio(cuit: str):
    """
    Obtiene el portfolio del cliente: familias confirmadas y disponibles

    Lógica:
    1. Consulta los subrubros únicos que el cliente ha comprado en los últimos 12 meses
    2. Mapea esos subrubros a familias confirmadas
    3. Retorna las familias no confirmadas como "disponibles"
    """
    try:
        supabase = get_supabase()

        # Calcular fecha de hace 12 meses
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # Obtener subrubros únicos del cliente
        response = supabase.table("ventas") \
            .select("subrubro") \
            .eq("cuit", cuit) \
            .gte("fecha", fecha_12_meses) \
            .execute()

        if not response.data:
            # Cliente sin compras recientes - todas las familias están disponibles
            familias_disponibles = [
                FamiliaDisponible(id=f["id"], nombre=f["nombre"], icono=f["icono"])
                for f in FAMILIAS_TODAS
            ]
            return PortfolioResponse(
                cuit=cuit,
                familias_confirmadas=[],
                familias_disponibles=familias_disponibles,
                total_familias_posibles=TOTAL_FAMILIAS,
                porcentaje_completado=0.0
            )

        # Obtener subrubros únicos
        subrubros_unicos = set(v.get("subrubro") for v in response.data if v.get("subrubro"))

        # Mapear subrubros a familias confirmadas
        familias_nombres_confirmadas = set()
        for subrubro in subrubros_unicos:
            familia = SUBRUBRO_A_FAMILIA.get(subrubro, subrubro)
            familias_nombres_confirmadas.add(familia)

        # Construir lista de familias confirmadas
        familias_confirmadas = []
        for familia_def in FAMILIAS_TODAS:
            if familia_def["nombre"] in familias_nombres_confirmadas:
                familias_confirmadas.append(FamiliaConfirmada(
                    id=familia_def["id"],
                    nombre=familia_def["nombre"],
                    subfamilias=familia_def["subfamilias"],
                    confirmada=True
                ))

        # Construir lista de familias disponibles (las que no están confirmadas)
        nombres_confirmados = {f.nombre for f in familias_confirmadas}
        familias_disponibles = [
            FamiliaDisponible(id=f["id"], nombre=f["nombre"], icono=f["icono"])
            for f in FAMILIAS_TODAS
            if f["nombre"] not in nombres_confirmados
        ]

        # Calcular porcentaje de completado
        porcentaje_completado = (len(familias_confirmadas) / TOTAL_FAMILIAS) * 100

        return PortfolioResponse(
            cuit=cuit,
            familias_confirmadas=familias_confirmadas,
            familias_disponibles=familias_disponibles,
            total_familias_posibles=TOTAL_FAMILIAS,
            porcentaje_completado=round(porcentaje_completado, 1)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener portfolio: {str(e)}")
