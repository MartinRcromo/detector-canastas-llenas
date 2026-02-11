import { CatalogFilters } from "@/lib/catalog/types";

interface SearchBarProps {
  filters: CatalogFilters;
}

export function SearchBar({ filters }: SearchBarProps) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <label className="mb-2 block text-sm font-medium text-slate-300" htmlFor="q">
        Búsqueda libre
      </label>
      <input
        id="q"
        name="q"
        defaultValue={filters.q ?? ""}
        placeholder="Ej: paragolpes Ford Ranger 2018 delantero"
        className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-emerald-500 focus:ring"
      />
    </div>
  );
}
