import { roundTo, safeDivide } from "@/lib/utils";

export type MetricasSubrubroInput = {
  subrubroId: number;
  ventasMonto: number;
  ventasCosto: number;
  ventasCantidad: number;
  stockUnidades: number;
  stockVolumenM3: number;
  stockValorizado: number;
};

export type GastosMensualesTotals = {
  cat1Total: number;
  cat2Total: number;
  cat3Total: number;
  cat4Total: number;
  otrosPct?: number;
};

export type AnalisisResultado = {
  subrubroId: number;
  porcentajeFacturacion: number;
  porcentajeVolumen: number;
  porcentajeCredito: number;
  porcentajeMarkup: number;
  gastoFacturacion: number;
  gastoVolumen: number;
  gastoCredito: number;
  gastoMarkup: number;
  gastoOtros: number;
  gastoTotal: number;
  margenBruto: number;
  resultado: number;
  markupMinimo: number;
  enPerdida: boolean;
  stockIdeal: number;
  stockExceso: number;
  mesesStock: number;
};

export function calculateResults(
  metricas: MetricasSubrubroInput[],
  gastos: GastosMensualesTotals
): AnalisisResultado[] {
  const totalVentas = metricas.reduce((acc, item) => acc + item.ventasMonto, 0);
  const totalVolumen = metricas.reduce((acc, item) => acc + item.stockVolumenM3, 0);
  const totalValorizado = metricas.reduce((acc, item) => acc + item.stockValorizado, 0);
  const totalMargenBruto = metricas.reduce((acc, item) => acc + (item.ventasMonto - item.ventasCosto), 0);
  const otrosFactor = gastos.otrosPct ?? 0.1;

  return metricas.map((item) => {
    const margenBruto = item.ventasMonto - item.ventasCosto;
    const porcentajeFacturacion = safeDivide(item.ventasMonto, totalVentas);
    const porcentajeVolumen = safeDivide(item.stockVolumenM3, totalVolumen);
    const porcentajeCredito = safeDivide(item.stockValorizado, totalValorizado);
    const porcentajeMarkup = safeDivide(margenBruto, totalMargenBruto);

    const gastoFacturacion = porcentajeFacturacion * gastos.cat1Total;
    const gastoVolumen = porcentajeVolumen * gastos.cat2Total;
    const gastoCredito = porcentajeCredito * gastos.cat3Total;
    const gastoMarkup = porcentajeMarkup * gastos.cat4Total;

    const gastoOtros = (gastoFacturacion + gastoVolumen + gastoCredito + gastoMarkup) * otrosFactor;
    const gastoTotal = gastoFacturacion + gastoVolumen + gastoCredito + gastoMarkup + gastoOtros;

    const markupMinimo = safeDivide(gastoTotal, item.ventasCantidad);
    const resultado = margenBruto - gastoTotal;

    const stockIdeal = Math.round((item.ventasCantidad / 6) * 3);
    const stockExceso = item.stockUnidades - stockIdeal;
    const mesesStock = safeDivide(item.stockUnidades, item.ventasCantidad / 6);

    return {
      subrubroId: item.subrubroId,
      porcentajeFacturacion: roundTo(porcentajeFacturacion, 8),
      porcentajeVolumen: roundTo(porcentajeVolumen, 8),
      porcentajeCredito: roundTo(porcentajeCredito, 8),
      porcentajeMarkup: roundTo(porcentajeMarkup, 8),
      gastoFacturacion: roundTo(gastoFacturacion, 2),
      gastoVolumen: roundTo(gastoVolumen, 2),
      gastoCredito: roundTo(gastoCredito, 2),
      gastoMarkup: roundTo(gastoMarkup, 2),
      gastoOtros: roundTo(gastoOtros, 2),
      gastoTotal: roundTo(gastoTotal, 2),
      margenBruto: roundTo(margenBruto, 2),
      resultado: roundTo(resultado, 2),
      markupMinimo: roundTo(markupMinimo, 2),
      enPerdida: resultado < 0,
      stockIdeal,
      stockExceso,
      mesesStock: roundTo(mesesStock, 2),
    };
  });
}
