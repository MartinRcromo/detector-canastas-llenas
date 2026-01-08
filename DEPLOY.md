# 🚀 Guía de Deployment en Netlify

## Opción 1: Desde la interfaz web de Netlify (Más fácil)

1. **Ir a Netlify**: https://app.netlify.com/
2. **Login/Signup** con tu cuenta de GitHub
3. **Click en**: "Add new site" → "Import an existing project"
4. **Autorizar GitHub** y seleccionar el repo: `MartinRcromo/detector-canastas-llenas`
5. **Configurar deployment**:
   - **Branch to deploy**: `claude/b2b-autoparts-platform-fz6SW`
   - **Build command**: `npm run build` (autodetectado)
   - **Publish directory**: `dist` (autodetectado)
6. **Click en**: "Deploy site"
7. **¡Listo!** En 1-2 minutos tendrás tu URL pública

### El archivo `netlify.toml` ya configura automáticamente:
- ✅ Build command
- ✅ Publish directory
- ✅ Redirects para React Router
- ✅ Headers de seguridad
- ✅ Cache optimizado
- ✅ Compresión de assets

---

## Opción 2: Desde la terminal con Netlify CLI

### Instalación (una sola vez):
```bash
npm install -g netlify-cli
```

### Desde tu máquina local:

```bash
# 1. Clonar/Pull del repo
git clone https://github.com/MartinRcromo/detector-canastas-llenas.git
# o si ya lo tenés:
git pull origin claude/b2b-autoparts-platform-fz6SW

# 2. Ir a la carpeta
cd detector-canastas-llenas

# 3. Instalar dependencias
npm install

# 4. Hacer build
npm run build

# 5. Login en Netlify
netlify login

# 6. Deploy a producción
netlify deploy --prod
```

**Seguí las instrucciones del CLI**:
- Te preguntará si querés crear un nuevo site o linkear uno existente
- Confirmá el build directory: `dist`
- ¡Listo!

---

## Opción 3: Deploy automático con GitHub

1. **Push a la rama**: Los cambios ya están pusheados
2. **Configurar en Netlify** (solo la primera vez):
   - Conectar el repo
   - Seleccionar branch: `claude/b2b-autoparts-platform-fz6SW`
3. **¡Auto-deploy!**: Cada push a esta rama desplegará automáticamente

---

## 🔍 Testing local antes de deploy:

```bash
# Build local
npm run build

# Preview del build
npm run preview
```

Esto levantará el build en: `http://localhost:4173`

---

## 📝 URLs después del deploy:

Netlify te dará URLs tipo:
- **Production**: `https://your-site-name.netlify.app`
- **Deploy previews**: `https://deploy-preview-123--your-site-name.netlify.app`

---

## ⚙️ Variables de entorno (si las necesitás más adelante):

En Netlify Dashboard:
1. Site settings → Environment variables
2. Agregar variables con prefijo `VITE_`
3. Ejemplo: `VITE_API_URL=https://api.example.com`

---

## 🎯 ¿Problemas?

### Build falla:
```bash
# Verificar que el build funcione localmente:
npm run build
```

### 404 en rutas:
- ✅ Ya está configurado en `netlify.toml` con los redirects

### Quiero cambiar el nombre del sitio:
- Site settings → Change site name

---

**¡Todo listo para deploy! 🚀**
