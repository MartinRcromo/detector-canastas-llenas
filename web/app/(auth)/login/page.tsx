export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-md space-y-6 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold text-white">Ingresar</h1>
          <p className="text-sm text-slate-400">
            Autenticación con Supabase para acceder a los tableros y cargas mensuales.
          </p>
        </div>
        <form className="space-y-4">
          <label className="flex flex-col gap-2 text-sm text-slate-200">
            Email
            <input
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              placeholder="usuario@empresa.com"
              type="email"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-200">
            Contraseña
            <input
              className="rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              placeholder="********"
              type="password"
            />
          </label>
          <button
            className="w-full rounded-md bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950"
            type="button"
          >
            Ingresar
          </button>
        </form>
      </div>
    </main>
  );
}
