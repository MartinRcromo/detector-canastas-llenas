import { parseNaturalQuery } from "@/lib/catalog/search";
import { CatalogFilters, ProductRow } from "@/lib/catalog/types";
import { createServerSupabaseClient } from "@/lib/supabase/server";

const PAGE_SIZE = 20;

function normalizeYearRange(yearRaw?: string) {
  if (!yearRaw) return null;
  const [from, to] = yearRaw.split("-").map((value) => Number(value.trim()));
  if (!Number.isNaN(from) && !Number.isNaN(to)) return { from, to };
  if (!Number.isNaN(from)) return { from, to: from };
  return null;
}

export async function searchCatalog(filters: CatalogFilters) {
  const supabase = createServerSupabaseClient();
  if (!supabase) {
    return { products: [], total: 0, page: Math.max(1, Number(filters.page ?? "1")), pageSize: PAGE_SIZE, hints: parseNaturalQuery(filters.q) };
  }
  const hints = parseNaturalQuery(filters.q);

  const page = Math.max(1, Number(filters.page ?? "1"));
  const pageFrom = (page - 1) * PAGE_SIZE;
  const pageTo = pageFrom + PAGE_SIZE - 1;

  const category = filters.category || hints.category;
  const make = filters.make || hints.make;
  const model = filters.model || hints.model;
  const position = filters.position || hints.position;
  const side = filters.side || hints.side;
  const year = filters.year || hints.year;
  const yearRange = normalizeYearRange(year);

  let query = supabase
    .from("products")
    .select(
      `
      id, sku, title, part_category, brand_vehicle, part_position, part_side, oem_codes, aftermarket_codes, specs,
      product_fitments!inner(id,make,model,year_from,year_to,trim,engine,engine_code,body_style,notes),
      product_images(id,path,is_primary,sort_order)
    `,
      { count: "exact" },
    )
    .eq("is_active", true)
    .order("created_at", { ascending: false })
    .range(pageFrom, pageTo);

  if (category) query = query.eq("part_category", category);
  if (make) query = query.or(`brand_vehicle.eq.${make},product_fitments.make.eq.${make}`);
  if (model) query = query.eq("product_fitments.model", model);
  if (position) query = query.eq("part_position", position);
  if (side) query = query.eq("part_side", side);
  if (filters.trim) query = query.ilike("product_fitments.trim", `%${filters.trim}%`);
  if (filters.engine || hints.engine) {
    const engineValue = filters.engine || hints.engine;
    query = query.or(`product_fitments.engine.ilike.%${engineValue}%,product_fitments.engine_code.ilike.%${engineValue}%`);
  }
  if (filters.bodyStyle) query = query.eq("product_fitments.body_style", filters.bodyStyle);
  if (filters.variant) query = query.ilike("specs->>variant", `%${filters.variant}%`);

  if (yearRange) {
    query = query.or(`year_from.is.null,year_from.lte.${yearRange.to}`, { foreignTable: "product_fitments" });
    query = query.or(`year_to.is.null,year_to.gte.${yearRange.from}`, { foreignTable: "product_fitments" });
  }

  if (filters.q) {
    const term = filters.q.trim();
    query = query.or(
      [
        `title.ilike.%${term}%`,
        `sku.ilike.%${term}%`,
        `oem_codes.cs.{${term}}`,
        `aftermarket_codes.cs.{${term}}`,
        `product_fitments.model.ilike.%${term}%`,
        `product_fitments.engine.ilike.%${term}%`,
        `product_fitments.engine_code.ilike.%${term}%`,
      ].join(","),
    );
  }

  const { data, count, error } = await query;

  if (error) {
    throw new Error(`Catalog query failed: ${error.message}`);
  }

  return {
    products: (data ?? []) as ProductRow[],
    total: count ?? 0,
    page,
    pageSize: PAGE_SIZE,
    hints,
  };
}
