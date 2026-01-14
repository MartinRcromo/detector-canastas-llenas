"""
Endpoint para el portfolio del cliente
GET /api/portfolio/{cuit}
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from database import execute_query
from models.responses import PortfolioResponse, FamiliaConfirmada, FamiliaDisponible

router = APIRouter()

# Todas las familias posibles basadas en rubros reales de la BD
FAMILIAS_TODAS = [
    {"id": 1, "nombre": "ILUMINACION", "icono": "Lightbulb", "subfamilias": "(faros, luces, lámparas)"},
    {"id": 2, "nombre": "CERRAJERIA", "icono": "Key", "subfamilias": "(cerraduras, llaves)"},
    {"id": 3, "nombre": "SISTEMA TERMICO", "icono": "Wind", "subfamilias": "(radiadores, termostatos)"},
    {"id": 4, "nombre": "PARAGOLPES / PIEZAS PLASTICAS", "icono": "Box", "subfamilias": "(paragolpes, guardabarros)"},
    {"id": 5, "nombre": "SISTEMA MOTRIZ", "icono": "Cog", "subfamilias": "(motor, transmisión)"},
    {"id": 6, "nombre": "ESPEJOS", "icono": "Eye", "subfamilias": "(espejos retrovisores)"},
    {"id": 7, "nombre": "EQUIPAMIENTO EXTERIOR", "icono": "Package", "subfamilias": "(molduras, accesorios)"},
    {"id": 8, "nombre": "SISTEMA ELECTRICO", "icono": "Zap", "subfamilias": "(alternadores, baterías)"},
    {"id": 9, "nombre": "ACCESORIOS", "icono": "Plus", "subfamilias": "(varios)"},
    {"id": 10, "nombre": "EMERGENCIA / SEGURIDAD", "icono": "AlertTriangle", "subfamilias": "(matafuegos, balizas)"},
    {"id": 11, "nombre": "EQUIPAMIENTO INTERIOR", "icono": "Home", "subfamilias": "(tapizados, consolas)"},
    {"id": 12, "nombre": "CARROCERIA", "icono": "Layers", "subfamilias": "(chapas, paneles)"},
    {"id": 13, "nombre": "SUSPENSION", "icono": "Activity", "subfamilias": "(amortiguadores, resortes)"},
    {"id": 14, "nombre": "MERCHANDISING", "icono": "Gift", "subfamilias": "(promocionales)"},
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
        # Calcular anio_mes de hace 12 meses
        anio_mes_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m")

        # Obtener rubros únicos del cliente (usamos rubro en lugar de subrubro)
        query = """
            SELECT DISTINCT rubro FROM ventas
            WHERE cuit = :cuit
            AND anio_mes >= :anio_mes_12_meses
            AND rubro IS NOT NULL
        """

        rubros_data = execute_query(query, {"cuit": cuit, "anio_mes_12_meses": anio_mes_12_meses})

        if not rubros_data:
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

        # Obtener rubros únicos
        rubros_unicos = set(v.get("rubro") for v in rubros_data if v.get("rubro"))

        # Los rubros son las familias confirmadas
        familias_nombres_confirmadas = rubros_unicos

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
