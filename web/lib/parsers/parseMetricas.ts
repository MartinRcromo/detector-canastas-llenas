import * as XLSX from "xlsx";
import { normalizePeriod } from "@/lib/utils";

export type MetricasRow = {
  subrubro: string;
  empresa: string;
  stockUnidades: number;
  ventasMonto: number;
  ventasCosto: number;
  markupReal: number;
  stockVolumenM3: number;
  stockIdeal: number;
  stockExceso: number;
  stockValorizado: number;
  stockMeses: number;
  ventasCantidad: number;
};

export type MetricasPayload = {
  periodo: string;
  rows: MetricasRow[];
};

const headerMap: Record<string, keyof MetricasRow> = {
  "articulo sub rubro": "subrubro",
  empresa: "empresa",
  "stock - unidades": "stockUnidades",
  "ventas - monto": "ventasMonto",
  "ventas - costo": "ventasCosto",
  "mark-up": "markupReal",
  "stock - volumen": "stockVolumenM3",
  "stock ideal": "stockIdeal",
  reducir: "stockExceso",
  "stock - valorizado (costo)": "stockValorizado",
  "meses stock": "stockMeses",
  "ventas - cantidad": "ventasCantidad",
};

export function parseMetricas(buffer: ArrayBuffer): MetricasPayload {
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheet = workbook.Sheets["Analisis x Subrubro"] ?? workbook.Sheets[workbook.SheetNames[0]];
  if (!sheet) {
    throw new Error("No se encontró la hoja 'Analisis x Subrubro'.");
  }

  const periodCell = sheet["B1"]?.v?.toString() ?? "";
  const periodo = normalizePeriod(periodCell);

  const rows = XLSX.utils.sheet_to_json<Record<string, string | number>>(sheet, {
    defval: "",
    range: 1,
  });

  const parsed = rows
    .map((row) => {
      const mapped: Partial<MetricasRow> = {};
      Object.entries(row).forEach(([key, value]) => {
        const normalized = key.toString().trim().toLowerCase();
        const mappedKey = headerMap[normalized];
        if (!mappedKey) return;
        if (typeof value === "number") {
          mapped[mappedKey] = value;
        } else {
          const asNumber = Number(value.toString().replace(/\./g, "").replace(/,/g, "."));
          mapped[mappedKey] = Number.isFinite(asNumber) ? asNumber : value.toString().trim();
        }
      });
      return mapped as MetricasRow;
    })
    .filter((row) => row.subrubro);

  return { periodo, rows: parsed };
}
