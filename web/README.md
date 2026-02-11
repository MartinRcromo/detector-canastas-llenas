# Catálogo Autopartes (Next.js + Supabase)

MVP B2B para búsqueda por lenguaje natural + filtros de compatibilidad (marca/modelo/año/motor/carrocería), catálogo web y exportación PDF.

## 1) Plan de arquitectura

- **Frontend**: Next.js 14 (App Router) + Tailwind.
  - `/catalog`: buscador, filtros, cards y paginación.
  - `/catalog/print`: layout A4 imprimible para export.
- **Backend en Next**:
  - `lib/catalog/query.ts`: armado de filtros SQL vía Supabase.
  - `lib/catalog/search.ts`: parser liviano de lenguaje natural (categoría/marca/modelo/año/posición/lado/motor).
  - `/api/catalog/pdf`: render HTML → PDF con Playwright.
- **DB/Storage**: Supabase Postgres + buckets públicos.
  - Tablas: `products`, `product_fitments`, `product_images`.
  - Bucket imágenes: `product-images`.
  - Bucket PDF: `catalogs`.

## 2) Checklist de setup (paso a paso)

### A. Instalar dependencias

```bash
cd web
npm install
```

### B. Variables de entorno

```bash
cp .env.example .env.local
```

Editar `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://TU-PROYECTO.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=TU_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=TU_SERVICE_ROLE_KEY
APP_BASE_URL=http://localhost:3000
```

### C. Crear tablas + índices + RLS

En Supabase SQL Editor ejecutar:

```sql
-- copiar contenido de db/migrations/001_catalog_schema.sql
```

### D. Crear buckets de Storage

En SQL Editor:

```sql
insert into storage.buckets (id, name, public)
values ('product-images', 'product-images', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('catalogs', 'catalogs', true)
on conflict (id) do nothing;
```

### E. Cargar seed (24 productos ejemplo)

```bash
npm run seed
```

### F. Levantar app

```bash
npm run dev
```

Abrir `http://localhost:3000/catalog`.

### G. Exportar PDF

- Descarga directa: botón **Exportar PDF directo**.
- Guardar en Storage: botón **Generar y guardar en Storage** (devuelve URL pública).

## 3) Implementación por etapas (junior-friendly)

1. **Modelo de datos**: primero creamos tablas separadas para productos, compatibilidades e imágenes.
2. **Parser natural**: detecta palabras clave (`ranger`, `2018`, `delantero`, `izq`, etc.) y las convierte en filtros.
3. **Consulta catálogo**: mezcla filtros explícitos + hints del parser y busca en `products` y `product_fitments`.
4. **UI catálogo**: formulario GET (fácil de debuggear), cards y paginado de 20 resultados.
5. **Vista print**: misma data, formato limpio para PDF.
6. **PDF endpoint**: Playwright abre `/catalog/print?...`, genera PDF y:
   - descarga directa, o
   - subida a `catalogs` en Supabase Storage.

## Scripts útiles

```bash
npm run seed
npm run upload:image -- <product_id> <ruta_local_imagen>
```

## Troubleshooting Playwright

Si falla Chromium en server:

```bash
npx playwright install chromium
```

Si estás en entorno Docker/CI, asegurate de tener dependencias del sistema para Chromium.

## Supuestos y pendientes

- Se usa **lectura pública** para catálogo (MVP), sin backoffice CRUD.
- El filtro de texto usa `ILIKE` + arrays; para escala alta, está preparado para migrar a motor dedicado (ej. Meilisearch).
- Seed trae datos realistas de ejemplo, no catálogo productivo.
