"""
Modelos Pydantic para las respuestas de la API
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# ==================== PERFIL ====================

class CompraReciente(BaseModel):
    """Modelo para una compra reciente"""
    fecha: str
    codigo_articulo: str
    nombre_articulo: str
    cantidad: int
    monto: float
    subrubro: str

class PerfilResponse(BaseModel):
    """Respuesta del endpoint /api/perfil/{cuit}"""
    cuit: str
    nombre_empresa: str
    clasificacion: str  # "Activo Plus", "Activo", "En desarrollo", etc.
    facturacion_anual: float
    unidades_compradas: int
    cantidad_pedidos: int
    subrubros_activos: int
    compras_recientes: List[CompraReciente]

# ==================== PORTFOLIO ====================

class FamiliaConfirmada(BaseModel):
    """Familia que el cliente ya maneja"""
    id: int
    nombre: str
    subfamilias: str
    confirmada: bool = True

class FamiliaDisponible(BaseModel):
    """Familia disponible para agregar"""
    id: int
    nombre: str
    icono: str

class PortfolioResponse(BaseModel):
    """Respuesta del endpoint /api/portfolio/{cuit}"""
    cuit: str
    familias_confirmadas: List[FamiliaConfirmada]
    familias_disponibles: List[FamiliaDisponible]
    total_familias_posibles: int
    porcentaje_completado: float

# ==================== OPORTUNIDADES ====================

class ProductoSugerido(BaseModel):
    """Producto individual sugerido"""
    codigo: str
    nombre: str
    precio: float
    demanda: str  # "Alta", "Media", "Baja"
    clasificacion_abc: str  # "AA", "A", "B", "C"
    volumen_12m: int  # Unidades vendidas últimos 12 meses
    precio_total: float  # Precio * cantidad mínima sugerida

class EstrategiaProductos(BaseModel):
    """Estrategia de productos (Quiero probar / Me tengo fe)"""
    tipo: str  # "probar" o "fe"
    productos: List[ProductoSugerido]
    monto_total_minimo: float
    monto_total_maximo: float
    cantidad_productos: int
    descripcion: str

class OportunidadFamilia(BaseModel):
    """Oportunidad de cross-selling por familia"""
    id: int
    familia: str
    razon: str
    potencial_mensual: float
    productos_sugeridos: int
    prioridad: str  # "alta", "media", "baja"
    productos: List[ProductoSugerido]  # Mantener para retrocompatibilidad
    estrategia_probar: EstrategiaProductos  # Solo AA
    estrategia_fe: EstrategiaProductos  # AA + A

class ProductoDestacado(BaseModel):
    """Producto destacado individual"""
    codigo: str
    nombre: str
    familia: str
    precio: float
    margen: float
    rotacion: str
    razon: str

class OportunidadesResponse(BaseModel):
    """Respuesta del endpoint /api/oportunidades/{cuit}"""
    cuit: str
    oportunidades_familias: List[OportunidadFamilia]
    productos_destacados: List[ProductoDestacado]
    total_potencial_mensual: float

# ==================== PLANES ====================

class TierBeneficio(BaseModel):
    """Beneficio de un tier"""
    descripcion: str

class Tier(BaseModel):
    """Información de un tier del programa"""
    nombre: str
    color: str  # Tailwind gradient classes
    borderColor: str
    iconColor: str
    rango: str
    objetivo: float
    descuento: str
    beneficios: List[str]

class PlanesResponse(BaseModel):
    """Respuesta del endpoint /api/planes/{cuit}"""
    cuit: str
    facturacion_anual: float
    tier_actual: str
    tiers: List[Tier]
    siguiente_tier: Optional[str]
    brecha_siguiente: Optional[float]
    porcentaje_progreso: Optional[float]
