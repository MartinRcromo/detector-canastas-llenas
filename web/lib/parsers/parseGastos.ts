import * as XLSX from "xlsx";
import { normalizePeriod } from "@/lib/utils";

export type GastosResumen = {
  periodo: string;
  cat1Total: number;
  cat2Total: number;
  cat3Total: number;
  cat4Total: number;
};

export type GastosDetalleRow = {
  empresa: string;
  sectorGrupo: string;
  sector: string;
  tipoGasto: string;
  proveedor: string;
  empresaTipo: string;
  monto: number;
  porcentajeGasto: number;
  porcentajePart: number;
  analisis: string;
  verificar: string | boolean;
};

export type GastosPayload = {
  resumen: GastosResumen;
  detalle: GastosDetalleRow[];
};

export function parseGastos(buffer: ArrayBuffer): GastosPayload {
  const workbook = XLSX.read(buffer, { type: "array" });

  const resumenSheet = workbook.Sheets["Resumen"] ?? workbook.Sheets[workbook.SheetNames[0]];
  const detalleSheet = workbook.Sheets["Detalle"] ?? workbook.Sheets[workbook.SheetNames[1]];

  if (!resumenSheet || !detalleSheet) {
    throw new Error("No se encontraron las hojas 'Resumen' y 'Detalle'.");
  }

  const periodoRaw = resumenSheet["B1"]?.v?.toString() ?? "";
  const periodo = normalizePeriod(periodoRaw);

  const getValueByLabel = (label: string) => {
    const rows = XLSX.utils.sheet_to_json<Record<string, string | number>>(resumenSheet, {
      header: 1,
      defval: "",
    });
    const found = rows.find((row) => row[0]?.toString().trim().toLowerCase() === label.toLowerCase());
    if (!found) return 0;
    const value = Number(found[1].toString().replace(/\./g, "").replace(/,/g, "."));
    return Number.isFinite(value) ? value : 0;
  };

  const resumen: GastosResumen = {
    periodo,
    cat1Total: getValueByLabel("Facturacion"),
    cat2Total: getValueByLabel("Volumen"),
    cat3Total: getValueByLabel("Credito"),
    cat4Total: getValueByLabel("Rentabilidad"),
  };

  const detalleRows = XLSX.utils.sheet_to_json<Record<string, string | number>>(detalleSheet, { defval: "" });
  const detalle = detalleRows.map((row) => ({
    empresa: row["Empresa"]?.toString() ?? "",
    sectorGrupo: row["Sector Grupo"]?.toString() ?? "",
    sector: row["Sector"]?.toString() ?? "",
    tipoGasto: row["Tipo Gasto"]?.toString() ?? "",
    proveedor: row["Proveedor"]?.toString() ?? "",
    empresaTipo: row["Empresa Tipo"]?.toString() ?? "",
    monto: Number(row["Gastos monto"] ?? 0),
    porcentajeGasto: Number(row["% Gasto"] ?? 0),
    porcentajePart: Number(row["% Part."] ?? 0),
    analisis: row["Analisis"]?.toString() ?? "",
    verificar: row["Verificar"] ?? "",
  }));

  return { resumen, detalle };
}
