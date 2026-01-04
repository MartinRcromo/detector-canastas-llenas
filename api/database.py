"""
Configuración de conexión a Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")

# Cliente de Supabase (singleton)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase() -> Client:
    """
    Retorna el cliente de Supabase configurado
    """
    return supabase
