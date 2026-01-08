"""
Sistema de caché simple en memoria con TTL (Time To Live)
Para clasificaciones ABC y estrategias de productos
"""
from datetime import datetime, timedelta
from typing import Any, Optional
import threading

class SimpleCache:
    """Caché thread-safe con TTL"""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutos por defecto
        self.cache = {}
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no expiró"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if datetime.now() < expiry:
                    return value
                else:
                    # Expiró, eliminar
                    del self.cache[key]
            return None

    def set(self, key: str, value: Any):
        """Guarda un valor en el caché con TTL"""
        with self.lock:
            expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)
            self.cache[key] = (value, expiry)

    def clear(self):
        """Limpia todo el caché"""
        with self.lock:
            self.cache.clear()

    def clear_expired(self):
        """Limpia solo los items expirados"""
        with self.lock:
            now = datetime.now()
            expired_keys = [k for k, (_, expiry) in self.cache.items() if now >= expiry]
            for key in expired_keys:
                del self.cache[key]


# Instancias globales de caché
clasificaciones_cache = SimpleCache(ttl_seconds=600)  # 10 minutos para clasificaciones ABC
estrategias_cache = SimpleCache(ttl_seconds=300)  # 5 minutos para estrategias
