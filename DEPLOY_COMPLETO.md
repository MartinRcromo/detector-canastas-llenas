# 🚀 Guía Completa de Deployment

Esta guía te ayudará a deployar el proyecto completo: Backend (Railway) + Frontend (Netlify) + Database (Supabase).

## 📋 Pre-requisitos

- [x] Cuenta en GitHub
- [ ] Cuenta en Railway (https://railway.app)
- [ ] Cuenta en Supabase (https://supabase.com)
- [x] Cuenta en Netlify (ya configurada: https://canasata-llena.netlify.app)

---

## 🗄️ PASO 1: Configurar Base de Datos (Supabase)

### 1.1 Crear Proyecto en Supabase

1. Ir a https://supabase.com
2. Click en "New Project"
3. Completar:
   - **Name**: `canastas-llenas`
   - **Database Password**: (guardar en lugar seguro)
   - **Region**: South America (São Paulo)
4. Esperar 2-3 minutos a que se cree el proyecto

### 1.2 Crear Tabla `ventas`

1. En Supabase, ir a "SQL Editor"
2. Ejecutar este script:

```sql
-- Crear tabla de ventas
CREATE TABLE ventas (
  id BIGSERIAL PRIMARY KEY,
  cuit VARCHAR(11) NOT NULL,
  cliente VARCHAR(255) NOT NULL,
  fecha DATE NOT NULL,
  empresa VARCHAR(50) NOT NULL,
  subrubro VARCHAR(100) NOT NULL,
  articulo_codigo VARCHAR(50) NOT NULL,
  articulo_nombre VARCHAR(255) NOT NULL,
  cantidad INTEGER NOT NULL DEFAULT 0,
  monto DECIMAL(12,2) NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para mejorar performance
CREATE INDEX idx_ventas_cuit ON ventas(cuit);
CREATE INDEX idx_ventas_fecha ON ventas(fecha DESC);
CREATE INDEX idx_ventas_empresa ON ventas(empresa);
CREATE INDEX idx_ventas_subrubro ON ventas(subrubro);

-- Comentarios
COMMENT ON TABLE ventas IS 'Registro de todas las ventas de las empresas del grupo';
COMMENT ON COLUMN ventas.cuit IS 'CUIT del cliente (sin guiones)';
COMMENT ON COLUMN ventas.empresa IS 'Empresa del grupo: CANASATA o SURTIHOGAR';
```

### 1.3 Obtener Credenciales

1. En Supabase, ir a **Settings → API**
2. Copiar:
   - **Project URL** (ejemplo: `https://abcdefgh.supabase.co`)
   - **anon public key** (comienza con `eyJ...`)
3. **Guardar estas credenciales** para el siguiente paso

### 1.4 Cargar Datos de Prueba (Opcional)

```sql
-- Insertar datos de ejemplo
INSERT INTO ventas (cuit, cliente, fecha, empresa, subrubro, articulo_codigo, articulo_nombre, cantidad, monto)
VALUES
  ('20301234567', 'DISTRIBUIDORA NORTE SA', '2024-01-15', 'CANASATA', 'Frenos', 'FR-001', 'Pastilla Freno Delantera', 10, 45000),
  ('20301234567', 'DISTRIBUIDORA NORTE SA', '2024-01-20', 'CANASATA', 'Suspensión', 'SU-120', 'Amortiguador Gas', 5, 38000),
  ('20301234567', 'DISTRIBUIDORA NORTE SA', '2024-02-10', 'CANASATA', 'Filtros', 'FI-450', 'Filtro Aceite Premium', 20, 32000);
```

---

## 🔧 PASO 2: Deploy del Backend (Railway)

### 2.1 Conectar Railway con GitHub

1. Ir a https://railway.app
2. Click en "Login" → "Login with GitHub"
3. Autorizar Railway

### 2.2 Crear Proyecto desde GitHub

1. Click en "New Project"
2. Seleccionar "Deploy from GitHub repo"
3. Buscar y seleccionar: **`MartinRcromo/detector-canastas-llenas`**
4. Railway comenzará a analizar el repositorio

### 2.3 Configurar el Servicio

1. Railway detectará que es un proyecto Python
2. En el servicio creado, ir a **Settings**
3. Configurar:

   **Root Directory:**
   ```
   api
   ```
   ⚠️ **CRÍTICO**: Esto le dice a Railway que la API está en la carpeta `api/`

4. Verificar que estos archivos fueron detectados:
   - ✅ `railway.json` (config de deploy)
   - ✅ `requirements.txt` (dependencias Python)
   - ✅ `Procfile` (comando de inicio)
   - ✅ `runtime.txt` (Python 3.11)

### 2.4 Configurar Variables de Entorno

1. En el servicio, click en **"Variables"**
2. Agregar estas 3 variables (usar los valores de Supabase):

```bash
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=eyJ... (tu anon key)
ENVIRONMENT=production
```

3. Click en "Add" para cada variable

### 2.5 Deployment Automático

1. Railway comenzará el deploy automáticamente
2. Ver logs en tiempo real (tab "Deployments")
3. Esperar hasta ver: **"✓ Deployment successful"**
4. El health check verificará que el endpoint `/health` responda

### 2.6 Obtener URL del Backend

1. En el servicio, ir a **Settings → Domains**
2. Click en **"Generate Domain"**
3. Railway creará una URL pública:
   ```
   https://tu-backend-production-XXXX.up.railway.app
   ```
4. **COPIAR ESTA URL** (la necesitarás para el frontend)

### 2.7 Verificar que Funciona

Abrir en el navegador:

1. **Health Check:**
   ```
   https://tu-backend.up.railway.app/health
   ```
   Debe mostrar:
   ```json
   {
     "status": "ok",
     "timestamp": "2024-01-...",
     "environment": "production"
   }
   ```

2. **Documentación Interactiva:**
   ```
   https://tu-backend.up.railway.app/docs
   ```
   Debe abrir la interfaz Swagger UI

3. **Probar un Endpoint:**
   ```
   https://tu-backend.up.railway.app/api/perfil/20301234567
   ```
   Debe retornar JSON con el perfil del cliente

✅ **Si todos los endpoints responden, el backend está funcionando correctamente!**

---

## 🌐 PASO 3: Conectar Frontend con Backend (Netlify)

### 3.1 Configurar Variable de Entorno en Netlify

1. Ir a https://app.netlify.com
2. Abrir el sitio: **canasata-llena**
3. Ir a **Site settings → Environment variables**
4. Click en **"Add a variable"**
5. Agregar:
   ```
   Key: VITE_API_URL
   Value: https://tu-backend.up.railway.app
   ```
   (Usar la URL de Railway del paso 2.6)

6. Click en **"Save"**

### 3.2 Redeploy el Frontend

Netlify debe hacer redeploy automático cuando detecta cambios en las variables de entorno. Si no:

1. Ir a **Deploys**
2. Click en **"Trigger deploy" → "Clear cache and deploy site"**
3. Esperar 2-3 minutos

### 3.3 Verificar Conexión Frontend-Backend

1. Abrir: https://canasata-llena.netlify.app
2. La app debe cargar sin errores
3. Abrir **DevTools (F12) → Console**
4. No debe haber errores de CORS
5. Verificar que los datos se cargan dinámicamente

**Prueba de funcionamiento:**
- Ir a la página "Perfil" → Debe mostrar datos reales de Supabase
- Ir a "Portfolio" → Debe mostrar familias detectadas
- Ir a "Oportunidades" → Debe calcular oportunidades en tiempo real
- Ir a "Planes" → Debe mostrar el tier calculado

---

## 🔐 Seguridad y CORS

El backend ya tiene configurado CORS para:
- ✅ `http://localhost:5173` (desarrollo local)
- ✅ `https://canasata-llena.netlify.app` (producción)

Si cambias el dominio de Netlify, debes actualizar `api/main.py`:

```python
origins = [
    "http://localhost:5173",
    "https://tu-nuevo-dominio.netlify.app",  # ← Actualizar aquí
]
```

Y hacer commit + push para que Railway redeploy automáticamente.

---

## 📊 Monitoreo y Logs

### Railway (Backend):
- **Logs en tiempo real**: Tab "Deployments" → Ver último deploy
- **Métricas**: CPU, RAM, Network Usage
- **Health Checks**: Cada 60 segundos verifica `/health`
- **Auto-restart**: Si falla, reintenta hasta 10 veces

### Netlify (Frontend):
- **Deploy logs**: Tab "Deploys" → Ver build logs
- **Analytics**: Si está habilitado
- **Function logs**: No aplica (solo frontend estático)

### Supabase (Database):
- **Logs**: Database → Logs
- **Performance**: Database → Reports
- **Usage**: Settings → Usage

---

## 🐛 Troubleshooting

### Error: "CORS policy blocked"
**Solución:** Verificar que la URL de Netlify esté en `api/main.py` → `origins`

### Error: "Failed to fetch"
**Solución:**
1. Verificar que `VITE_API_URL` esté configurado en Netlify
2. Verificar que Railway esté corriendo (status verde)
3. Probar el health check manualmente

### Error: "No se encontraron datos para el CUIT"
**Solución:**
1. Verificar que la tabla `ventas` tenga datos
2. Verificar credenciales de Supabase en Railway
3. Revisar logs de Railway para ver errores de conexión

### Error: "Module not found" en Railway
**Solución:**
1. Verificar que `Root Directory` sea `api`
2. Verificar que `requirements.txt` esté en `api/`
3. Redeploy desde cero

---

## ✅ Checklist Final

Antes de dar por terminado el deploy, verificar:

- [ ] Supabase: Tabla `ventas` creada con datos
- [ ] Railway: Backend corriendo (status verde)
- [ ] Railway: Variables de entorno configuradas
- [ ] Railway: URL pública generada
- [ ] Netlify: Variable `VITE_API_URL` configurada
- [ ] Netlify: Último deploy exitoso
- [ ] Frontend: Página carga sin errores
- [ ] Frontend: Datos se muestran dinámicamente
- [ ] CORS: No hay errores en DevTools
- [ ] Health check: `/health` responde OK

---

## 🎉 ¡Felicitaciones!

Tu aplicación B2B está completamente deployada y funcionando:

- ✅ **Frontend**: https://canasata-llena.netlify.app
- ✅ **Backend**: https://tu-backend.up.railway.app
- ✅ **Database**: Supabase PostgreSQL
- ✅ **Auto-deploy**: Cada push a GitHub despliega automáticamente
