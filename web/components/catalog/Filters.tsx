import { BODY_STYLES, CATEGORIES, MODELS, POSITIONS, SIDES, VEHICLE_MAKES } from "@/lib/catalog/constants";
import { CatalogFilters } from "@/lib/catalog/types";

interface FiltersProps {
  filters: CatalogFilters;
}

const baseInputClass =
  "w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-emerald-500 focus:ring";

function SelectField({ name, value, options }: { name: string; value?: string; options: readonly string[] }) {
  return (
    <select name={name} defaultValue={value ?? ""} className={baseInputClass}>
      <option value="">Todos</option>
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}

export function Filters({ filters }: FiltersProps) {
  return (
    <div className="grid gap-3 rounded-lg border border-slate-700 bg-slate-900 p-4 md:grid-cols-4">
      <SelectField name="category" value={filters.category} options={CATEGORIES} />
      <SelectField name="make" value={filters.make} options={VEHICLE_MAKES} />
      <SelectField name="model" value={filters.model} options={MODELS} />
      <input name="year" defaultValue={filters.year ?? ""} placeholder="Año o rango (2018 o 2016-2019)" className={baseInputClass} />
      <input name="trim" defaultValue={filters.trim ?? ""} placeholder="Versión / Trim" className={baseInputClass} />
      <input name="engine" defaultValue={filters.engine ?? ""} placeholder="Motor / código" className={baseInputClass} />
      <SelectField name="bodyStyle" value={filters.bodyStyle} options={BODY_STYLES} />
      <SelectField name="position" value={filters.position} options={POSITIONS} />
      <SelectField name="side" value={filters.side} options={SIDES} />
      <input name="variant" defaultValue={filters.variant ?? ""} placeholder="Variante (PDC, lavafaros...)" className={baseInputClass} />
    </div>
  );
}
