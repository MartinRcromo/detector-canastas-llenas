create extension if not exists "pgcrypto";

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  sku text unique not null,
  title text not null,
  part_category text not null,
  brand_vehicle text not null,
  part_position text,
  part_side text,
  oem_codes text[],
  aftermarket_codes text[],
  barcode text,
  uom text not null default 'UN',
  is_active boolean not null default true,
  specs jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.product_fitments (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  make text not null,
  model text not null,
  model_generation text,
  year_from int,
  year_to int,
  trim text,
  engine text,
  engine_code text,
  transmission text,
  body_style text,
  doors int,
  market text,
  notes text,
  created_at timestamptz not null default now()
);

create table if not exists public.product_images (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  path text not null,
  is_primary boolean not null default false,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_products_part_category on public.products (part_category);
create index if not exists idx_products_brand_vehicle on public.products (brand_vehicle);
create index if not exists idx_products_sku on public.products (sku);
create index if not exists idx_products_specs_gin on public.products using gin (specs);

create index if not exists idx_product_fitments_make_model on public.product_fitments (make, model);
create index if not exists idx_product_fitments_years on public.product_fitments (year_from, year_to);
create index if not exists idx_product_fitments_engine_code on public.product_fitments (engine_code);
create index if not exists idx_product_fitments_product_id on public.product_fitments (product_id);

create index if not exists idx_product_images_product_id on public.product_images (product_id);
create index if not exists idx_product_images_is_primary on public.product_images (is_primary);

alter table public.products enable row level security;
alter table public.product_fitments enable row level security;
alter table public.product_images enable row level security;

create policy if not exists "Public read products" on public.products for select to anon, authenticated using (true);
create policy if not exists "Public read product_fitments" on public.product_fitments for select to anon, authenticated using (true);
create policy if not exists "Public read product_images" on public.product_images for select to anon, authenticated using (true);
