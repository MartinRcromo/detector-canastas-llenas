import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    periodo: "2025-01",
    resumen: {
      total_subrubros: 378,
      subrubros_perdida: 127,
      perdida_total: -1245000000,
      beneficio_total: 4832000000,
      resultado_neto: 3587000000,
      vs_mes_anterior: {
        subrubros_perdida: -5,
        perdida_total: 124000000,
        beneficio_total: 423000000,
        resultado_neto: 298000000,
      },
    },
    top_peores: [],
    top_mejores: [],
    evolucion_6_meses: [],
    distribucion_gastos: {
      cat1: 6794000000,
      cat2: 4478000000,
      cat3: 1939000000,
      cat4: 819000000,
    },
  });
}
