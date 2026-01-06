"""
API Backend para Detector de Canastas Llenas
FastAPI + SQLAlchemy + PostgreSQL
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

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

# Testing endpoints
@app.get("/api/test/clientes")
def test_list_clientes():
    """Lista los primeros 20 clientes con más ventas"""
    from database import execute_query

    query = """
        SELECT
            cuit,
            cliente,
            COUNT(*) as cantidad_registros,
            SUM(importe) as total_importe
        FROM public.ventas
        WHERE empresa IN ('Cromo', 'BBA')
        GROUP BY cuit, cliente
        ORDER BY total_importe DESC
        LIMIT 20
    """

    try:
        result = execute_query(query)
        return {
            "total_clientes_encontrados": len(result),
            "clientes": result
        }
    except Exception as e:
        return {"error": str(e), "tipo": str(type(e))}

@app.get("/api/test/estructura")
def test_estructura_tabla():
    """Muestra la estructura de la tabla ventas"""
    from database import execute_query

    query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'ventas'
        ORDER BY ordinal_position
    """

    try:
        result = execute_query(query)
        return {"columnas": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/test/empresas")
def test_list_empresas():
    """Lista todas las empresas únicas en la tabla ventas"""
    from database import execute_query

    query = """
        SELECT
            empresa,
            COUNT(*) as total_registros,
            COUNT(DISTINCT cuit) as total_clientes,
            SUM(importe) as total_importe
        FROM public.ventas
        GROUP BY empresa
        ORDER BY total_registros DESC
    """

    try:
        result = execute_query(query)
        return {
            "total_empresas_encontradas": len(result),
            "empresas": result
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/test/clientes-sin-filtro")
def test_list_all_clientes():
    """Lista los primeros 20 clientes SIN filtrar por empresa"""
    from database import execute_query

    query = """
        SELECT
            empresa,
            cuit,
            cliente,
            COUNT(*) as cantidad_registros,
            SUM(importe) as total_importe
        FROM public.ventas
        GROUP BY empresa, cuit, cliente
        ORDER BY total_importe DESC
        LIMIT 20
    """

    try:
        result = execute_query(query)
        return {
            "total_encontrados": len(result),
            "clientes": result
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/test/perfil-debug/{cuit}")
def test_perfil_debug(cuit: str):
    """Debug endpoint para ver errores en perfil"""
    from database import execute_query
    from datetime import datetime, timedelta
    import traceback

    try:
        fecha_12_meses = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        query = """
            SELECT * FROM ventas
            WHERE cuit = :cuit
            AND fecha >= :fecha_12_meses
            ORDER BY fecha DESC
            LIMIT 5
        """

        ventas = execute_query(query, {"cuit": cuit, "fecha_12_meses": fecha_12_meses})

        return {
            "cuit": cuit,
            "fecha_12_meses": fecha_12_meses,
            "total_ventas": len(ventas),
            "primera_venta": ventas[0] if ventas else None,
            "columnas": list(ventas[0].keys()) if ventas else []
        }
    except Exception as e:
        return {
            "error": str(e),
            "tipo": str(type(e).__name__),
            "traceback": traceback.format_exc()
        }
