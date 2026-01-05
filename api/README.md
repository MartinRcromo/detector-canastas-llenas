# Detector Canastas Llenas - API Backend

API Backend FastAPI + SQLAlchemy + PostgreSQL para análisis de cross-selling B2B en distribuidora de autopartes.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y de alto rendimiento
- **SQLAlchemy** - ORM y conexión a PostgreSQL
- **PostgreSQL** - Base de datos relacional (Supabase)
- **Pydantic** - Validación de datos y modelos
- **Python nativo** - Análisis de datos sin pandas (optimizado para Railway)

## 📋 Endpoints

### GET `/health`
Health check del servidor
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00",
  "environment": "production"
}
```

### GET `/api/perfil/{cuit}`
Obtiene el perfil completo del cliente
- Facturación anual (últimos 12 meses)
- Clasificación del cliente
- Métricas de compra
- Compras recientes

### GET `/api/portfolio/{cuit}`
Obtiene el portfolio del cliente
- Familias confirmadas (que ya compra)
- Familias disponibles (que puede agregar)
- Porcentaje de completado

### GET `/api/oportunidades/{cuit}`
Identifica oportunidades de cross-selling
- Familias recomendadas basadas en clientes similares
- Productos top por familia
- Productos destacados
- Potencial de facturación estimado

### GET `/api/planes/{cuit}`
Planes de activación comercial (tiers)
- Tier actual del cliente
- Beneficios de cada tier
- Progreso hacia el siguiente nivel
- Brecha de facturación

## 🛠️ Instalación Local

1. **Instalar dependencias**
```bash
cd api
pip install -r requirements.txt
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Editar `.env` con tu URL de PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
ENVIRONMENT=development
```

3. **Ejecutar servidor de desarrollo**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- API: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## 📊 Estructura de la Base de Datos

### Tabla `ventas`
Columnas requeridas:
- `cuit` (string) - CUIT del cliente
- `cliente` (string) - Nombre de la empresa
- `fecha` (date) - Fecha de la venta
- `empresa` (string) - Empresa del grupo (CANASATA/SURTIHOGAR)
- `subrubro` (string) - Familia/subrubro del producto
- `articulo_codigo` (string) - Código del artículo
- `articulo_nombre` (string) - Nombre del artículo
- `cantidad` (int) - Cantidad vendida
- `monto` (float) - Monto total de la venta

## 🚢 Deploy en Railway (RECOMENDADO)

### Archivos de Configuración Incluidos:
- ✅ `railway.json` - Configuración de build y deploy
- ✅ `Procfile` - Comando de inicio
- ✅ `runtime.txt` - Python 3.11
- ✅ `requirements.txt` - Dependencias

### Pasos Detallados:

1. **Crear cuenta en Railway**
   - Visitar https://railway.app
   - Conectar con GitHub

2. **Crear nuevo proyecto**
   - Click en "New Project"
   - Seleccionar "Deploy from GitHub repo"
   - Buscar: `MartinRcromo/detector-canastas-llenas`
   - Railway detectará automáticamente el proyecto

3. **Configurar el servicio**
   - En Settings del servicio:
     - **Root Directory**: `api` ⚠️ IMPORTANTE
     - Start Command: Auto-detectado desde `railway.json`
     - Health Check: `/health` (configurado automáticamente)

4. **Configurar variables de entorno**
   - Click en "Variables" en el servicio
   - Agregar:
     ```
     DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require
     ENVIRONMENT=production
     ```

   **Obtener DATABASE_URL desde Supabase:**
   1. Ir a https://supabase.com
   2. Abrir tu proyecto
   3. Settings → Database → Connection String → URI
   4. Copiar la connection string completa (modo "Session")

5. **Deploy automático**
   - Railway hace build automático
   - Health check en `/health` verifica el deployment
   - Auto-restart si falla (máx 10 reintentos)

6. **Obtener URL del servicio**
   - Settings → Domains → Generate Domain
   - Copiar URL: `https://tu-api.up.railway.app`
   - **Guardar esta URL para el frontend**

7. **Verificar deployment**
   - Health: `https://tu-api.up.railway.app/health`
   - Docs: `https://tu-api.up.railway.app/docs`

### Monitoreo y Logs:
- Logs en tiempo real en Railway dashboard
- Métricas de CPU/RAM/Network
- Health checks cada 60 segundos

## 🚢 Deploy en Render

1. **Crear cuenta en Render**
   - Visitar https://render.com
   - Conectar con GitHub

2. **Crear nuevo Web Service**
   - New → Web Service
   - Conectar repositorio

3. **Configurar servicio**
   - Name: `canastas-llenas-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Root Directory: `api`

4. **Variables de entorno**
   - Agregar en Environment:
     - `DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require`
     - `ENVIRONMENT=production`

5. **Deploy**
   - Create Web Service
   - Render hará deploy automático

## 🔧 Algoritmos de Análisis

### Co-ocurrencia de Familias
1. Identifica clientes similares por facturación (±30%)
2. Calcula matriz de co-ocurrencia de familias
3. Detecta familias que el cliente NO tiene pero clientes similares SÍ
4. Rankea por score de co-ocurrencia

### Estimación de Potencial
- Calcula promedio de facturación mensual de la familia
- Basado en clientes similares que la compran
- Ajustado por tamaño del cliente

### Clasificación de Clientes
- **Activo Plus**: >$3M anual
- **Activo**: $1.5M - $3M anual
- **En desarrollo**: $500K - $1.5M anual
- **Nuevo**: <$500K anual

## 📝 Notas de Desarrollo

- La API usa análisis de los últimos 12 meses
- Solo considera empresas del grupo (CANASATA, SURTIHOGAR)
- El benchmark se basa en clientes con facturación similar (±30%)
- Mínimo de co-ocurrencia: 5 clientes para considerar oportunidad válida

## 🔗 Actualizar Frontend

Una vez deployada la API, actualizar el frontend en `src/config/api.js`:

```javascript
const API_URL = process.env.REACT_APP_API_URL || 'https://tu-api.railway.app';

export const fetchPerfil = async (cuit) => {
  const response = await fetch(`${API_URL}/api/perfil/${cuit}`);
  return response.json();
};
```

Y agregar al CORS en `main.py` la URL de producción de la API.
