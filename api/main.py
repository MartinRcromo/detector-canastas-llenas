"""
API Backend para Detector de Canastas Llenas
FastAPI + Supabase
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Importar database
from database import get_supabase

# Importar routers
from routes import perfil, portfolio, oportunidades, planes

# Crear aplicación FastAPI
app = FastAPI(
    title="Detector Canastas Llenas API",
    description="API para análisis de cross-selling B2B en distribuidora de autopartes",
    version="1.0.0"
)

# Configurar CORS para Netlify
origins = [
    "http://localhost:5173",  # Dev local
    "http://localhost:4173",  # Preview local
    "https://canasata-llena.netlify.app",  # Producción Netlify
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/health")
async def health_check():
    """
    Endpoint de health check para verificar que la API está funcionando
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production")
    }

# Incluir routers
app.include_router(perfil.router, tags=["Perfil"])
app.include_router(portfolio.router, tags=["Portfolio"])
app.include_router(oportunidades.router, tags=["Oportunidades"])
app.include_router(planes.router, tags=["Planes"])

# Root endpoint
@app.get("/")
async def root():
    """
    Endpoint raíz con información de la API
    """
    return {
        "message": "Detector Canastas Llenas API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "perfil": "/api/perfil/{cuit}",
            "portfolio": "/api/portfolio/{cuit}",
            "oportunidades": "/api/oportunidades/{cuit}",
            "planes": "/api/planes/{cuit}"
        },
        "docs": "/docs"
    }
