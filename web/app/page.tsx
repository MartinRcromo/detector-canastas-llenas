import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-400">Rentabilidad por subrubro</p>
        <h1 className="text-3xl font-semibold text-white md:text-5xl">Panel de control</h1>
        <p className="max-w-xl text-base text-slate-300">
          Cargá los archivos mensuales y analizá la distribución de gastos, resultados y oportunidades de acción.
        </p>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          className="rounded-md bg-emerald-500 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
          href="/dashboard"
        >
          Ir al dashboard
        </Link>
        <Link
          className="rounded-md border border-slate-700 px-5 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-500"
          href="/upload"
        >
          Subir datos
        </Link>
      </div>
    </main>
  );
}
