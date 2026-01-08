# Portal B2B - Distribuidora Autopartes

Plataforma web B2B para análisis comercial y cross-selling en distribución de autopartes.

## 🚀 Stack Tecnológico

- **React 18** - Framework UI
- **Vite** - Build tool
- **Tailwind CSS** - Estilos
- **React Router v6** - Navegación
- **Lucide React** - Iconos

## 🎨 Paleta de Colores

### Primarios
- **Azul Industrial**: `#1E3A5F` (confianza, profesionalismo)
- **Gris Grafito**: `#2D3748` (solidez)

### Secundarios
- **Naranja Mecánico**: `#F56B2A` (acción, oportunidades)
- **Verde Progreso**: `#10B981` (completado, positivo)
- **Amarillo Alerta**: `#F59E0B` (atención)

### Neutros
- **Blanco**: `#FFFFFF`
- **Gris Claro**: `#F7FAFC`
- **Gris Medio**: `#E2E8F0`
- **Gris Texto**: `#4A5568`

## 📦 Instalación

```bash
# Instalar dependencias
npm install

# Ejecutar servidor de desarrollo
npm run dev

# Build para producción
npm run build
```

## 🎯 Funcionalidades

### ✅ Implementado
1. **Mi Perfil** - Vista completa del perfil comercial con métricas y clasificación

### 🔜 Próximamente
2. **Portfolio** - Análisis detallado de productos por categoría
3. **Oportunidades** - Recomendaciones de cross-selling
4. **Planes** - Sistema de tiers y beneficios escalonados

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   ├── Badge.jsx
│   ├── Button.jsx
│   ├── Card.jsx
│   ├── Header.jsx
│   ├── Layout.jsx
│   ├── MetricCard.jsx
│   ├── ProgressBar.jsx
│   └── Sidebar.jsx
├── pages/              # Páginas principales
│   ├── ProfilePage.jsx
│   ├── PortfolioPage.jsx
│   ├── OpportunitiesPage.jsx
│   └── PlansPage.jsx
├── utils/              # Utilidades
│   └── formatters.js
├── App.jsx            # Router principal
├── main.jsx          # Entry point
└── index.css         # Estilos globales
```

## 🧩 Componentes UI

- **Button** - Botones con variantes (primary, secondary, outline)
- **Card** - Tarjetas contenedoras con título opcional
- **Badge** - Etiquetas de estado/categoría
- **MetricCard** - Tarjetas para métricas con iconos
- **ProgressBar** - Barras de progreso animadas
- **Layout** - Layout principal con Header y Sidebar

## 🎨 Diseño

- **Desktop first** con diseño responsive
- **Sidebar colapsable** en mobile
- **Animaciones suaves** con Tailwind
- **Sistema de colores** profesional para B2B

## 📝 Notas

- Todos los datos están **hardcodeados** como constantes
- No hay conexión a backend en esta versión
- Enfocado en UI/UX y navegación

---

**Versión**: 1.0.0
**Última actualización**: Enero 2024
