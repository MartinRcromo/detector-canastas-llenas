export type Json = string | number | boolean | null | { [key: string]: Json } | Json[];

export interface ProductRow {
  id: string;
  sku: string;
  title: string;
  part_category: string;
  brand_vehicle: string;
  part_position: string | null;
  part_side: string | null;
  oem_codes: string[] | null;
  aftermarket_codes: string[] | null;
  specs: Record<string, Json>;
  product_fitments: ProductFitmentRow[];
  product_images: ProductImageRow[];
}

export interface ProductFitmentRow {
  id: string;
  make: string;
  model: string;
  year_from: number | null;
  year_to: number | null;
  trim: string | null;
  engine: string | null;
  engine_code: string | null;
  body_style: string | null;
  notes: string | null;
}

export interface ProductImageRow {
  id: string;
  path: string;
  is_primary: boolean;
  sort_order: number;
}

export interface CatalogFilters {
  q?: string;
  category?: string;
  make?: string;
  model?: string;
  year?: string;
  trim?: string;
  engine?: string;
  bodyStyle?: string;
  position?: string;
  side?: string;
  variant?: string;
  page?: string;
}

export interface ParsedQueryHints {
  category?: string;
  make?: string;
  model?: string;
  position?: string;
  side?: string;
  year?: string;
  engine?: string;
}
