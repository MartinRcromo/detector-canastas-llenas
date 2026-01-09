const cards = [
  {
    title: "Subrubros en pérdida",
    value: "127 / 378 (33.6%)",
    delta: "↓ -5 vs mes anterior",
  },
  {
    title: "Pérdida total",
    value: "-$1.245M",
    delta: "↑ +$124M vs anterior",
  },
  {
    title: "Beneficio total",
    value: "+$4.832M",
    delta: "↑ +$423M vs anterior",
  },
  {
    title: "Resultado neto",
    value: "+$3.587M",
    delta: "↑ +$298M vs anterior",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-2">
        <h2 className="text-2xl font-semibold text-white">Resumen ejecutivo</h2>
        <p className="text-sm text-slate-400">
          Vista consolidada del desempeño mensual con foco en subrubros críticos y oportunidades.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {cards.map((card) => (
          <div key={card.title} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{card.title}</p>
            <p className="mt-3 text-2xl font-semibold text-white">{card.value}</p>
            <p className="mt-2 text-sm text-emerald-300">{card.delta}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="text-lg font-semibold text-white">Top 10 peores performers</h3>
          <p className="mt-2 text-sm text-slate-400">
            Ordenados por resultado negativo con alerta visual para pérdidas críticas.
          </p>
          <div className="mt-4 space-y-3 text-sm text-slate-200">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="flex items-center justify-between rounded-lg bg-slate-950/60 px-3 py-2">
                <span>Subrubro {index + 1}</span>
                <span className="text-rose-300">-$120M</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <h3 className="text-lg font-semibold text-white">Top 10 mejores performers</h3>
          <p className="mt-2 text-sm text-slate-400">
            Ordenados por resultado positivo con indicadores de eficiencia de stock.
          </p>
          <div className="mt-4 space-y-3 text-sm text-slate-200">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="flex items-center justify-between rounded-lg bg-slate-950/60 px-3 py-2">
                <span>Subrubro {index + 1}</span>
                <span className="text-emerald-300">+$210M</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
