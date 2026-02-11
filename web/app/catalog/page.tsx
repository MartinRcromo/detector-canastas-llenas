import { Filters } from "@/components/catalog/Filters";
import { Pagination } from "@/components/catalog/Pagination";
import { PdfActions } from "@/components/catalog/PdfActions";
import { ProductCard } from "@/components/catalog/ProductCard";
import { SearchBar } from "@/components/catalog/SearchBar";
import { searchCatalog } from "@/lib/catalog/query";
import { CatalogFilters } from "@/lib/catalog/types";

interface CatalogPageProps {
  searchParams: CatalogFilters;
}

export default async function CatalogPage({ searchParams }: CatalogPageProps) {
  const result = await searchCatalog(searchParams);

  const queryParams = new URLSearchParams();
  Object.entries(searchParams).forEach(([key, value]) => {
    if (key !== "page" && value) queryParams.set(key, value);
  });

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-4 p-6">
      <h1 className="text-2xl font-bold text-slate-100">Catálogo Autopartes B2B</h1>
      <form className="space-y-3">
        <SearchBar filters={searchParams} />
        <Filters filters={searchParams} />
        <div className="flex flex-wrap gap-2">
          <button type="submit" className="rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400">
            Buscar
          </button>
          <a href="/catalog" className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800">
            Limpiar
          </a>
          <a href={`/catalog/print?${queryParams.toString()}`} className="rounded-md border border-slate-600 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800">
            Vista imprimible
          </a>
          <PdfActions queryString={queryParams.toString()} />
        </div>
      </form>
      <p className="text-sm text-slate-400">
        Sugerencias detectadas: {Object.entries(result.hints).map(([k, v]) => `${k}:${v}`).join(" | ") || "sin hints"}
      </p>
      <section className="grid gap-3">
        {result.products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </section>
      <Pagination page={result.page} total={result.total} pageSize={result.pageSize} queryString={queryParams.toString()} />
    </main>
  );
}
