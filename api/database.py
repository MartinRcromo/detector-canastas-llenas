"""
Configuración de conexión a PostgreSQL usando SQLAlchemy
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# DATABASE_URL con fallback (Railway-friendly)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.hqyuqslepvholsarirbg:J4h28fsLRj21WOUZ@aws-0-us-west-2.pooler.supabase.com:5432/postgres?sslmode=require"
)

# Crear engine con configuración para Railway
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Railway funciona mejor sin connection pooling
    connect_args={"sslmode": "require"},
    echo=False  # Set True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Retorna una sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def execute_query(query, params=None):
    """
    Ejecuta una query SQL y retorna los resultados como lista de dicts

    Args:
        query: Query SQL (puede usar :param_name para parámetros)
        params: Diccionario con parámetros para la query

    Returns:
        Lista de diccionarios con los resultados
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

def execute_scalar(query, params=None):
    """
    Ejecuta una query y retorna un solo valor escalar

    Args:
        query: Query SQL
        params: Diccionario con parámetros

    Returns:
        Valor escalar o None
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), params or {})
        row = result.fetchone()
        return row[0] if row else None
