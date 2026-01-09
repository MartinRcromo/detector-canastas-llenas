import { roundTo, safeDivide } from "@/lib/utils";

export type SimulationInputs = {
  ventasMonto: number;
  ventasCosto: number;
  ventasCantidad: number;
  markupReal: number;
  stockUnidades: number;
  stockVolumenM3: number;
  stockValorizado: number;
  gastoFacturacion: number;
  gastoVolumen: number;
  gastoCredito: number;
  gastoMarkup: number;
  gastoOtros: number;
  totalVolumenPeriodo: number;
  totalValorizadoPeriodo: number;
  gastosCat2Total: number;
  gastosCat3Total: number;
};

export type SimulationParams = {
  deltaMarkupPct: number;
  reduccionStockPct: number;
  deltaPrecio: number;
};

export type SimulationResult = {
  actual: {
    resultado: number;
    markupReal: number;
    gastoTotal: number;
    mesesStock: number;
  };
  proyectado: {
    resultado: number;
    markupReal: number;
    gastoTotal: number;
    ahorroVolumen: number;
    ahorroCredito: number;
  };
};

export function simulateChanges(inputs: SimulationInputs, params: SimulationParams): SimulationResult {
  const nuevoPrecioUnitario = inputs.ventasMonto / inputs.ventasCantidad + params.deltaPrecio;
  const nuevoMarkup = inputs.markupReal + params.deltaMarkupPct;
  const nuevoStockUnidades = inputs.stockUnidades * (1 - params.reduccionStockPct / 100);

  const nuevasVentasMonto = nuevoPrecioUnitario * inputs.ventasCantidad;
  const nuevoMargenBruto = nuevasVentasMonto - inputs.ventasCosto;

  const nuevoStockVolumen = inputs.stockVolumenM3 * (1 - params.reduccionStockPct / 100);
  const nuevoStockValorizado = inputs.stockValorizado * (1 - params.reduccionStockPct / 100);

  const nuevaPorcVolumen = safeDivide(nuevoStockVolumen, inputs.totalVolumenPeriodo);
  const nuevaPorcCredito = safeDivide(nuevoStockValorizado, inputs.totalValorizadoPeriodo);

  const nuevoGastoVolumen = nuevaPorcVolumen * inputs.gastosCat2Total;
  const nuevoGastoCredito = nuevaPorcCredito * inputs.gastosCat3Total;

  const nuevoGastoTotal =
    inputs.gastoFacturacion + nuevoGastoVolumen + nuevoGastoCredito + inputs.gastoMarkup + inputs.gastoOtros;

  const nuevoResultado = nuevoMargenBruto - nuevoGastoTotal;

  const actualGastoTotal =
    inputs.gastoFacturacion + inputs.gastoVolumen + inputs.gastoCredito + inputs.gastoMarkup + inputs.gastoOtros;

  const actualResultado = inputs.ventasMonto - inputs.ventasCosto - actualGastoTotal;
  const mesesStock = safeDivide(inputs.stockUnidades, inputs.ventasCantidad / 6);

  return {
    actual: {
      resultado: roundTo(actualResultado, 2),
      markupReal: roundTo(inputs.markupReal, 2),
      gastoTotal: roundTo(actualGastoTotal, 2),
      mesesStock: roundTo(mesesStock, 2),
    },
    proyectado: {
      resultado: roundTo(nuevoResultado, 2),
      markupReal: roundTo(nuevoMarkup, 2),
      gastoTotal: roundTo(nuevoGastoTotal, 2),
      ahorroVolumen: roundTo(inputs.gastoVolumen - nuevoGastoVolumen, 2),
      ahorroCredito: roundTo(inputs.gastoCredito - nuevoGastoCredito, 2),
    },
  };
}
