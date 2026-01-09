export default function UploadPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Carga mensual</h2>
        <p className="text-sm text-slate-400">
          Cargá los archivos de métricas y gastos para recalcular los resultados del período.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-6">
          <p className="text-sm font-semibold text-slate-200">Archivo de subrubros</p>
          <p className="mt-2 text-xs text-slate-400">Analisis_de_subrubro_Margen_minimo.xlsx</p>
          <button className="mt-4 rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200">
            Seleccionar archivo
          </button>
        </div>
        <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/40 p-6">
          <p className="text-sm font-semibold text-slate-200">Archivo de gastos</p>
          <p className="mt-2 text-xs text-slate-400">Analisis_Gastos_Dividir_x_Subrubro.xlsx</p>
          <button className="mt-4 rounded-md border border-slate-700 px-3 py-2 text-xs text-slate-200">
            Seleccionar archivo
          </button>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-lg font-semibold text-white">Estado de procesamiento</h3>
        <p className="mt-2 text-sm text-slate-400">
          Una vez cargados, el sistema validará período, columnas y ejecutará el cálculo automático.
        </p>
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-800">
          <div className="h-full w-1/3 bg-emerald-500" />
        </div>
      </div>
    </div>
  );
}
