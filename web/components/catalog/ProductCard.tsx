import { ProductRow } from "@/lib/catalog/types";

interface ProductCardProps {
  product: ProductRow;
  compact?: boolean;
}

function getImageUrl(path?: string) {
  if (!path) return "/placeholder-part.svg";
  if (path.startsWith("http")) return path;

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!supabaseUrl) return "/placeholder-part.svg";

  return `${supabaseUrl}/storage/v1/object/public/product-images/${path}`;
}

export function ProductCard({ product, compact = false }: ProductCardProps) {
  const image = product.product_images.find((item) => item.is_primary) ?? product.product_images[0];
  const fitments = product.product_fitments.slice(0, 2);
  const specs = (product.specs ?? {}) as Record<string, unknown>;

  return (
    <article className="grid gap-4 rounded-lg border border-slate-700 bg-slate-900 p-4 md:grid-cols-[140px_1fr]">
      <img src={getImageUrl(image?.path)} alt={product.title} className="h-36 w-full rounded-md object-cover" />
      <div className="space-y-2">
        <p className="text-xs text-emerald-400">SKU: {product.sku}</p>
        <h3 className="text-base font-semibold text-slate-100">{product.title}</h3>
        <p className="text-sm text-slate-300">
          OEM: {(product.oem_codes ?? []).slice(0, 3).join(" · ") || "-"} | ALT: {(product.aftermarket_codes ?? []).slice(0, 2).join(" · ") || "-"}
        </p>
        <div className="text-sm text-slate-300">
          {fitments.map((fitment) => (
            <p key={fitment.id}>
              {fitment.make} {fitment.model} {fitment.year_from ?? ""}-{fitment.year_to ?? ""} | Motor {fitment.engine ?? "N/D"} | {fitment.body_style ?? "N/D"}
              {fitment.notes ? ` | ${fitment.notes}` : ""}
            </p>
          ))}
        </div>
        {!compact && (
          <p className="text-sm text-slate-300">
            Posición: {product.part_position ?? "N/D"} | Lado: {product.part_side ?? "N/D"} | Material: {(specs.material as string) ?? "N/D"} |
            Finish: {(specs.finish as string) ?? "N/D"} | Variante: {(specs.variant as string) ?? "N/D"}
          </p>
        )}
      </div>
    </article>
  );
}
