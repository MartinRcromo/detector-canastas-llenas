"""
Configuración de conexión a PostgreSQL usando SQLAlchemy
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL debe estar configurado en .env")

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
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
