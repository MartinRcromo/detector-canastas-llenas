import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, Trash2, Plus, Minus, ArrowLeft, CheckCircle, TrendingUp, Award } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useCliente } from '../context/ClienteContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import { formatCurrency, formatNumber } from '../utils/formatters';

const CartPage = () => {
  const navigate = useNavigate();
  const { items, itemsPorSubrubro, actualizarCantidad, eliminarProducto, vaciarCarrito, calcularTotal } = useCart();
  const { cuit } = useCliente();
  const { data: planes } = useApi(() => api.getPlanes(cuit), [cuit]);
  const { data: perfil } = useApi(() => api.getPerfil(cuit), [cuit]);

  const [confirmarVaciado, setConfirmarVaciado] = useState(false);

  if (items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card className="text-center py-12">
          <ShoppingCart className="w-20 h-20 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-bold text-gray-graphite mb-2">
            Tu carrito está vacío
          </h2>
          <p className="text-gray-text mb-6">
            Explorá las oportunidades y agregá productos a tu carrito
          </p>
          <Button
            variant="primary"
            onClick={() => navigate('/oportunidades')}
          >
            Ver Oportunidades
          </Button>
        </Card>
      </div>
    );
  }

  // Calcular totales
  const subtotal = calcularTotal();
  const facturacionAnual = perfil?.facturacion_anual || 0;
  const facturacionProyectada = facturacionAnual + (subtotal * 12); // Proyección anual

  // Determinar tier actual y siguiente
  const tierActual = planes?.tier_actual || 'Bronze';
  const tiers = planes?.tiers || [];
  const tierActualData = tiers.find(t => t.nombre === tierActual);
  const siguienteTierData = tiers.find(t => t.nombre === planes?.siguiente_tier);

  // Calcular descuento según tier
  const obtenerDescuento = (tier) => {
    const descuentos = {
      'Bronze': 0,
      'Silver': 5,
      'Gold': 10,
      'Platinum': 15,
      'Diamond': 20,
      'Premium': 25
    };
    return descuentos[tier] || 0;
  };

  const descuentoActual = obtenerDescuento(tierActual);
  const descuentoMonto = subtotal * (descuentoActual / 100);
  const totalConDescuento = subtotal - descuentoMonto;

  // Calcular progreso hacia siguiente tier
  const progresoHaciaSiguienteTier = siguienteTierData
    ? Math.min((facturacionProyectada / siguienteTierData.objetivo) * 100, 100)
    : 100;

  const faltaParaSiguienteTier = siguienteTierData
    ? Math.max(siguienteTierData.objetivo - facturacionProyectada, 0)
    : 0;

  const itemsAgrupados = itemsPorSubrubro();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-blue-industrial mb-2">
            🛒 Mi Carrito de Compras
          </h1>
          <p className="text-sm sm:text-base text-gray-text">
            {items.length} productos seleccionados de {Object.keys(itemsAgrupados).length} subrubros
          </p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            onClick={() => navigate('/oportunidades')}
            className="flex items-center gap-2 flex-1 sm:flex-initial"
          >
            <ArrowLeft size={18} />
            <span className="hidden sm:inline">Seguir comprando</span>
            <span className="sm:hidden">Volver</span>
          </Button>
          {confirmarVaciado ? (
            <div className="flex gap-2 flex-1 sm:flex-initial">
              <Button
                variant="outline"
                onClick={() => setConfirmarVaciado(false)}
                className="flex-1 sm:flex-initial text-sm"
              >
                Cancelar
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  vaciarCarrito();
                  setConfirmarVaciado(false);
                }}
                className="flex-1 sm:flex-initial bg-red-600 hover:bg-red-700 text-sm"
              >
                Confirmar
              </Button>
            </div>
          ) : (
            <Button
              variant="outline"
              onClick={() => setConfirmarVaciado(true)}
              className="flex items-center gap-2 text-red-600 border-red-600 hover:bg-red-50"
            >
              <Trash2 size={18} />
              <span className="hidden sm:inline">Vaciar carrito</span>
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de productos */}
        <div className="lg:col-span-2 space-y-4">
          {Object.entries(itemsAgrupados).map(([subrubro, productos]) => (
            <Card key={subrubro}>
              <h3 className="text-lg font-bold text-blue-industrial mb-4 border-b pb-2">
                {subrubro}
                <span className="ml-2 text-sm font-normal text-gray-text">
                  ({productos.length} productos)
                </span>
              </h3>

              <div className="space-y-3">
                {productos.map(item => (
                  <div
                    key={item.codigo}
                    className="flex flex-col sm:flex-row gap-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-start gap-2 mb-2">
                        <Badge className={
                          item.clasificacion_abc === 'AA'
                            ? 'bg-green-100 text-green-800 text-xs'
                            : 'bg-blue-100 text-blue-800 text-xs'
                        }>
                          {item.clasificacion_abc}
                        </Badge>
                        <Badge className="bg-gray-200 text-gray-700 text-xs capitalize">
                          {item.estrategia === 'probar' ? '🎯 Quiero probar' : item.estrategia === 'fe' ? '🚀 Me tengo fe' : 'Sugerido'}
                        </Badge>
                      </div>
                      <p className="font-medium text-blue-industrial text-sm sm:text-base">
                        {item.codigo}
                      </p>
                      <p className="text-xs sm:text-sm text-gray-text mt-1">
                        {item.nombre}
                      </p>
                      <p className="text-xs text-gray-500 mt-1 hidden sm:block">
                        {formatNumber(item.volumen_12m)} u/12m
                      </p>
                    </div>

                    <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-3 sm:gap-2">
                      <div className="flex items-center gap-2 order-2 sm:order-1">
                        <button
                          onClick={() => actualizarCantidad(item.codigo, item.cantidad - 1)}
                          className="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center bg-white border border-gray-300 rounded hover:bg-gray-100"
                        >
                          <Minus size={14} />
                        </button>
                        <span className="w-10 text-center font-semibold text-sm sm:text-base">
                          {item.cantidad}
                        </span>
                        <button
                          onClick={() => actualizarCantidad(item.codigo, item.cantidad + 1)}
                          className="w-7 h-7 sm:w-8 sm:h-8 flex items-center justify-center bg-white border border-gray-300 rounded hover:bg-gray-100"
                        >
                          <Plus size={14} />
                        </button>
                      </div>

                      <div className="text-right order-1 sm:order-2">
                        <p className="text-base sm:text-lg font-bold text-orange-mechanic">
                          {formatCurrency(item.precio * item.cantidad)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatCurrency(item.precio)} c/u
                        </p>
                      </div>

                      <button
                        onClick={() => eliminarProducto(item.codigo)}
                        className="order-3 text-red-600 hover:text-red-700 p-1"
                      >
                        <Trash2 size={16} className="sm:hidden" />
                        <Trash2 size={18} className="hidden sm:block" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>

        {/* Resumen y Tier */}
        <div className="lg:col-span-1 space-y-4">
          {/* Resumen de compra */}
          <Card className="sticky top-20">
            <h3 className="text-lg font-bold text-blue-industrial mb-4 border-b pb-2">
              Resumen de Compra
            </h3>

            <div className="space-y-3 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-text">Subtotal:</span>
                <span className="font-semibold">{formatCurrency(subtotal)}</span>
              </div>

              {descuentoActual > 0 && (
                <div className="flex justify-between text-sm text-green-600">
                  <span>Descuento {tierActual} ({descuentoActual}%):</span>
                  <span className="font-semibold">-{formatCurrency(descuentoMonto)}</span>
                </div>
              )}

              <div className="border-t pt-3">
                <div className="flex justify-between items-baseline">
                  <span className="text-base font-bold text-gray-graphite">Total:</span>
                  <span className="text-2xl font-bold text-orange-mechanic">
                    {formatCurrency(totalConDescuento)}
                  </span>
                </div>
              </div>
            </div>

            <Button
              variant="primary"
              className="w-full flex items-center justify-center gap-2"
              onClick={() => alert('Funcionalidad de checkout próximamente')}
            >
              <CheckCircle size={20} />
              Finalizar Pedido
            </Button>
          </Card>

          {/* Tier actual y progreso */}
          <Card className={`border-2 ${tierActualData?.borderColor || 'border-gray-300'}`}>
            <div className="flex items-center gap-3 mb-4">
              <Award className={`w-8 h-8 ${tierActualData?.iconColor || 'text-gray-500'}`} />
              <div>
                <p className="text-xs text-gray-text">Tu nivel actual</p>
                <p className="text-lg font-bold text-blue-industrial">{tierActual}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-text">Facturación anual actual:</span>
                  <span className="font-semibold">{formatCurrency(facturacionAnual)}</span>
                </div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-text">Con este pedido (proyección):</span>
                  <span className="font-semibold text-green-600">
                    +{formatCurrency(subtotal * 12)}
                  </span>
                </div>
                <div className="flex justify-between text-sm font-bold">
                  <span className="text-gray-text">Total proyectado:</span>
                  <span className="text-blue-industrial">{formatCurrency(facturacionProyectada)}</span>
                </div>
              </div>

              {siguienteTierData && (
                <>
                  <div className="border-t pt-3">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp size={16} className="text-orange-mechanic" />
                      <span className="text-sm font-semibold text-gray-graphite">
                        Progreso hacia {siguienteTierData.nombre}
                      </span>
                    </div>

                    <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                      <div
                        className="bg-gradient-to-r from-orange-mechanic to-orange-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${progresoHaciaSiguienteTier}%` }}
                      />
                    </div>

                    <div className="flex justify-between text-xs text-gray-text">
                      <span>{progresoHaciaSiguienteTier.toFixed(0)}% completado</span>
                      <span>Meta: {formatCurrency(siguienteTierData.objetivo)}</span>
                    </div>

                    {faltaParaSiguienteTier > 0 && (
                      <p className="text-xs text-gray-600 mt-2 bg-blue-50 p-2 rounded">
                        Te faltan <strong>{formatCurrency(faltaParaSiguienteTier)}</strong> para alcanzar {siguienteTierData.nombre} y obtener <strong>{siguienteTierData.descuento}</strong> de descuento
                      </p>
                    )}
                  </div>

                  {progresoHaciaSiguienteTier >= 100 && (
                    <div className="bg-green-50 border border-green-200 rounded p-3">
                      <p className="text-sm text-green-800 font-semibold flex items-center gap-2">
                        <CheckCircle size={16} />
                        ¡Felicitaciones! Alcanzaste el nivel {siguienteTierData.nombre}
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
