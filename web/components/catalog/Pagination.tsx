interface PaginationProps {
  page: number;
  total: number;
  pageSize: number;
  queryString: string;
}

export function Pagination({ page, total, pageSize, queryString }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm">
      <span className="text-slate-300">
        Página {page} de {totalPages} ({total} resultados)
      </span>
      <div className="flex gap-2">
        <a
          href={`/catalog?${queryString}&page=${Math.max(1, page - 1)}`}
          className="rounded-md border border-slate-600 px-3 py-1 text-slate-200 hover:bg-slate-800"
        >
          Anterior
        </a>
        <a
          href={`/catalog?${queryString}&page=${Math.min(totalPages, page + 1)}`}
          className="rounded-md border border-slate-600 px-3 py-1 text-slate-200 hover:bg-slate-800"
        >
          Siguiente
        </a>
      </div>
    </div>
  );
}
