import { ProductCard } from "@/components/catalog/ProductCard";
import { searchCatalog } from "@/lib/catalog/query";
import { CatalogFilters } from "@/lib/catalog/types";

interface CatalogPrintPageProps {
  searchParams: CatalogFilters;
}

export default async function CatalogPrintPage({ searchParams }: CatalogPrintPageProps) {
  const result = await searchCatalog({ ...searchParams, page: "1" });

  return (
    <main className="mx-auto max-w-4xl space-y-3 bg-white p-6 text-slate-900 print:p-0">
      <header className="mb-4 border-b border-slate-300 pb-3">
        <h1 className="text-xl font-bold">Catálogo Autopartes - Vista Imprimible</h1>
        <p className="text-xs text-slate-600">Filtros: {new URLSearchParams(searchParams as Record<string, string>).toString() || "sin filtros"}</p>
      </header>
      {result.products.map((product) => (
        <ProductCard key={product.id} product={product} compact />
      ))}
    </main>
  );
}
