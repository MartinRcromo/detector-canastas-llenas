import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, TrendingUp, Star, ChevronRight, ChevronDown, ChevronUp, ShoppingCart, Check } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
import { useCart } from '../context/CartContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency, formatNumber } from '../utils/formatters';

const OpportunitiesPage = () => {
  const navigate = useNavigate();
  const { cuit } = useCliente();
  const { agregarEstrategia } = useCart();
  const { data: oportunidades, loading, error } = useApi(() => api.getOportunidades(cuit), [cuit]);

  const [familiaExpandida, setFamiliaExpandida] = useState(null);
  const [estrategiaSeleccionada, setEstrategiaSeleccionada] = useState({}); // {familiaId: 'probar' | 'fe'}
  const [montoSlider, setMontoSlider] = useState({}); // {familiaId: montoActual}
  const [agregadoConfirmado, setAgregadoConfirmado] = useState({}); // {familiaId: true/false}

  if (loading) {
    return <Loading message="Analizando oportunidades de cross-selling..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Error al cargar oportunidades"
        message={error}
      />
    );
  }

  if (!oportunidades) {
    return null;
  }

  const toggleFamilia = (familiaId) => {
    setFamiliaExpandida(familiaExpandida === familiaId ? null : familiaId);
  };

  const seleccionarEstrategia = (familiaId, tipo) => {
    setEstrategiaSeleccionada(prev => ({
      ...prev,
      [familiaId]: tipo
    }));

    // Inicializar slider con monto mínimo cuando se selecciona "fe"
    if (tipo === 'fe') {
      const familia = oportunidades.oportunidades_familias.find(f => f.id === familiaId);
      if (familia) {
        setMontoSlider(prev => ({
          ...prev,
          [familiaId]: familia.estrategia_fe.monto_total_minimo
        }));
      }
    }
  };

  const actualizarMontoSlider = (familiaId, nuevoMonto) => {
    setMontoSlider(prev => ({
      ...prev,
      [familiaId]: nuevoMonto
    }));
  };

  const filtrarProductosPorMonto = (productos, montoMaximo) => {
    // Ordenar productos por clasificación (AA primero) y precio
    const productosOrdenados = [...productos].sort((a, b) => {
      if (a.clasificacion_abc === 'AA' && b.clasificacion_abc !== 'AA') return -1;
      if (a.clasificacion_abc !== 'AA' && b.clasificacion_abc === 'AA') return 1;
      return a.precio - b.precio;
    });

    // Agregar productos hasta alcanzar el monto
    const resultado = [];
    let montoAcumulado = 0;

    for (const producto of productosOrdenados) {
      if (montoAcumulado + producto.precio_total <= montoMaximo) {
        resultado.push(producto);
        montoAcumulado += producto.precio_total;
      }
    }

    return resultado;
  };

  const obtenerProductosSegunEstrategia = (opp) => {
    const estrategia = estrategiaSeleccionada[opp.id];

    if (!estrategia) {
      // Por defecto mostrar productos legacy
      return opp.productos;
    }

    if (estrategia === 'probar') {
      return opp.estrategia_probar.productos;
    }

    if (estrategia === 'fe') {
      const montoActual = montoSlider[opp.id] || opp.estrategia_fe.monto_total_minimo;
      return filtrarProductosPorMonto(opp.estrategia_fe.productos, montoActual);
    }

    return opp.productos;
  };

  const handleAgregarAlCarrito = (opp) => {
    const productos = obtenerProductosSegunEstrategia(opp);
    const estrategia = estrategiaSeleccionada[opp.id] || 'legacy';

    agregarEstrategia(productos, opp.familia, estrategia);

    // Mostrar confirmación
    setAgregadoConfirmado(prev => ({
      ...prev,
      [opp.id]: true
    }));

    // Ocultar confirmación después de 2 segundos
    setTimeout(() => {
      setAgregadoConfirmado(prev => ({
        ...prev,
        [opp.id]: false
      }));
    }, 2000);
  };

  const getPrioridadColor = (prioridad) => {
    return prioridad === 'alta'
      ? 'bg-orange-100 text-orange-800 border-orange-300'
      : 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const getDemandaColor = (demanda) => {
    const colors = {
      'Alta': 'bg-green-100 text-green-800',
      'Media': 'bg-blue-100 text-blue-800',
      'Baja': 'bg-gray-100 text-gray-800',
    };
    return colors[demanda] || 'bg-gray-100 text-gray-800';
  };

  const getRotacionColor = (rotacion) => {
    if (rotacion.includes('Muy')) return 'text-green-600';
    if (rotacion.includes('Alta')) return 'text-blue-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-blue-industrial mb-2">
          💡 Oportunidades de Cross-Selling
        </h1>
        <p className="text-gray-text">
          Productos y familias seleccionados para vos, basados en tu perfil y clientes similares
        </p>
      </div>

      {/* Resumen de Potencial */}
      <Card className="bg-gradient-to-r from-orange-50 to-yellow-50 border-2 border-orange-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-text mb-1">Potencial de crecimiento mensual</p>
            <p className="text-4xl font-bold text-orange-mechanic mb-2">
              {formatCurrency(oportunidades.total_potencial_mensual)}
            </p>
            <p className="text-sm text-gray-text">
              Basado en {oportunidades.oportunidades_familias.length} familias recomendadas
            </p>
          </div>
          <div className="hidden md:flex w-20 h-20 bg-orange-mechanic rounded-full items-center justify-center">
            <Lightbulb className="w-10 h-10 text-white" />
          </div>
        </div>
      </Card>

      {/* Familias Recomendadas */}
      {oportunidades.oportunidades_familias.length > 0 ? (
        <div>
          <h2 className="text-2xl font-bold text-blue-industrial mb-4">
            🎯 Nuevas Familias Recomendadas
          </h2>

          <div className="space-y-4">
            {oportunidades.oportunidades_familias.map((opp) => (
              <Card key={opp.id} className="hover:border-orange-mechanic border-2 border-transparent transition-all">
                <div
                  className="cursor-pointer"
                  onClick={() => toggleFamilia(opp.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold text-blue-industrial">
                          {opp.familia}
                        </h3>
                        <Badge className={`${getPrioridadColor(opp.prioridad)} border`}>
                          {opp.prioridad === 'alta' ? '🔥 Prioridad Alta' : '⭐ Recomendado'}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap gap-4 text-sm text-gray-text">
                        <span className="flex items-center gap-1">
                          <TrendingUp size={16} className="text-orange-mechanic" />
                          {formatCurrency(opp.potencial_mensual)}/mes
                        </span>
                        <span className="flex items-center gap-1">
                          <ShoppingCart size={16} className="text-blue-industrial" />
                          {opp.productos_sugeridos} productos
                        </span>
                      </div>

                      <p className="text-sm text-gray-text mt-2">
                        {opp.razon}
                      </p>
                    </div>

                    <div className="ml-4">
                      {familiaExpandida === opp.id ? (
                        <ChevronUp className="w-6 h-6 text-gray-text" />
                      ) : (
                        <ChevronDown className="w-6 h-6 text-gray-text" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Estrategias y productos de la familia (expandible) */}
                {familiaExpandida === opp.id && (
                  <div className="mt-4 pt-4 border-t-2 border-gray-light animate-fade-in space-y-4">
                    {/* Botones de estrategia */}
                    <div>
                      <h4 className="font-semibold text-gray-graphite mb-3">
                        Seleccioná tu estrategia:
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Botón "Quiero probar" */}
                        <button
                          onClick={() => seleccionarEstrategia(opp.id, 'probar')}
                          className={`p-4 rounded-lg border-2 transition-all text-left ${
                            estrategiaSeleccionada[opp.id] === 'probar'
                              ? 'border-blue-industrial bg-blue-50 shadow-md'
                              : 'border-gray-300 bg-white hover:border-blue-300'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="font-bold text-blue-industrial text-lg">
                              🎯 Quiero probar
                            </h5>
                            <Badge className="bg-blue-100 text-blue-800">AA</Badge>
                          </div>
                          <p className="text-sm text-gray-text mb-2">
                            {opp.estrategia_probar?.descripcion || 'Solo productos de máxima rotación'}
                          </p>
                          <p className="text-sm font-semibold text-blue-industrial">
                            {opp.estrategia_probar?.cantidad_productos || 0} productos · {formatCurrency(opp.estrategia_probar?.monto_total_minimo || 0)}
                          </p>
                        </button>

                        {/* Botón "Me tengo fe" */}
                        <button
                          onClick={() => seleccionarEstrategia(opp.id, 'fe')}
                          className={`p-4 rounded-lg border-2 transition-all text-left ${
                            estrategiaSeleccionada[opp.id] === 'fe'
                              ? 'border-orange-mechanic bg-orange-50 shadow-md'
                              : 'border-gray-300 bg-white hover:border-orange-300'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <h5 className="font-bold text-orange-mechanic text-lg">
                              🚀 Me tengo fe
                            </h5>
                            <Badge className="bg-orange-100 text-orange-800">AA + A</Badge>
                          </div>
                          <p className="text-sm text-gray-text mb-2">
                            {opp.estrategia_fe?.descripcion || 'Productos AA + A expandidos con slider'}
                          </p>
                          <p className="text-sm font-semibold text-orange-mechanic">
                            {opp.estrategia_fe?.cantidad_productos || 0} productos · {formatCurrency(opp.estrategia_fe?.monto_total_minimo || 0)} - {formatCurrency(opp.estrategia_fe?.monto_total_maximo || 0)}
                          </p>
                        </button>
                      </div>
                    </div>

                    {/* Slider de monto (solo para estrategia "Me tengo fe") */}
                    {estrategiaSeleccionada[opp.id] === 'fe' && opp.estrategia_fe && (
                      <div className="bg-orange-50 p-4 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <label className="font-semibold text-gray-graphite">
                            Ajustá tu inversión:
                          </label>
                          <span className="text-xl font-bold text-orange-mechanic">
                            {formatCurrency(montoSlider[opp.id] || opp.estrategia_fe.monto_total_minimo)}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={opp.estrategia_fe.monto_total_minimo}
                          max={opp.estrategia_fe.monto_total_maximo}
                          step={1000}
                          value={montoSlider[opp.id] || opp.estrategia_fe.monto_total_minimo}
                          onChange={(e) => actualizarMontoSlider(opp.id, parseFloat(e.target.value))}
                          className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer accent-orange-mechanic"
                        />
                        <div className="flex justify-between text-xs text-gray-text mt-1">
                          <span>Mínimo: {formatCurrency(opp.estrategia_fe.monto_total_minimo)}</span>
                          <span>Máximo: {formatCurrency(opp.estrategia_fe.monto_total_maximo)}</span>
                        </div>
                      </div>
                    )}

                    {/* Lista de productos según estrategia seleccionada */}
                    {estrategiaSeleccionada[opp.id] && (
                      <div>
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-gray-graphite">
                            Productos seleccionados ({obtenerProductosSegunEstrategia(opp).length}):
                          </h4>
                          <Button
                            variant={agregadoConfirmado[opp.id] ? "outline" : "primary"}
                            onClick={() => handleAgregarAlCarrito(opp)}
                            disabled={agregadoConfirmado[opp.id]}
                            className="flex items-center gap-2"
                          >
                            {agregadoConfirmado[opp.id] ? (
                              <>
                                <Check size={18} />
                                Agregado
                              </>
                            ) : (
                              <>
                                <ShoppingCart size={18} />
                                Agregar al carrito
                              </>
                            )}
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {obtenerProductosSegunEstrategia(opp).map((producto, idx) => (
                            <div
                              key={idx}
                              className="bg-white rounded-lg p-4 border-2 border-gray-200 hover:border-orange-mechanic transition-colors"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <Badge className={
                                      producto.clasificacion_abc === 'AA'
                                        ? 'bg-green-100 text-green-800 text-xs'
                                        : 'bg-blue-100 text-blue-800 text-xs'
                                    }>
                                      {producto.clasificacion_abc}
                                    </Badge>
                                    <Badge className={`${getDemandaColor(producto.demanda)} text-xs`}>
                                      {producto.demanda}
                                    </Badge>
                                  </div>
                                  <p className="font-medium text-blue-industrial text-sm">
                                    {producto.codigo}
                                  </p>
                                  <p className="text-xs text-gray-text mt-1">
                                    {producto.nombre}
                                  </p>
                                </div>
                              </div>
                              <div className="flex justify-between items-center mt-2">
                                <p className="text-lg font-bold text-orange-mechanic">
                                  {formatCurrency(producto.precio)}
                                </p>
                                <span className="text-xs text-gray-text">
                                  {formatNumber(producto.volumen_12m)} u/12m
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Mostrar productos legacy si no hay estrategia seleccionada */}
                    {!estrategiaSeleccionada[opp.id] && opp.productos && opp.productos.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-graphite mb-3">
                          Productos Sugeridos (seleccioná una estrategia arriba):
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 opacity-50">
                          {opp.productos.map((producto, idx) => (
                            <div
                              key={idx}
                              className="bg-gray-light rounded-lg p-4"
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex-1">
                                  <p className="font-medium text-blue-industrial text-sm">
                                    {producto.codigo}
                                  </p>
                                  <p className="text-xs text-gray-text mt-1">
                                    {producto.nombre}
                                  </p>
                                </div>
                                <Badge className={`${getDemandaColor(producto.demanda)} text-xs`}>
                                  {producto.demanda}
                                </Badge>
                              </div>
                              <p className="text-lg font-bold text-orange-mechanic">
                                {formatCurrency(producto.precio)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </div>
      ) : (
        <Card>
          <div className="text-center py-8 text-gray-text">
            <Lightbulb className="w-16 h-16 mx-auto mb-4 text-gray-medium" />
            <p className="text-lg font-medium mb-2">No hay oportunidades disponibles</p>
            <p className="text-sm">
              Continuá comprando y volvé más tarde para ver nuevas recomendaciones.
            </p>
          </div>
        </Card>
      )}

      {/* Productos Destacados */}
      {oportunidades.productos_destacados && oportunidades.productos_destacados.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-blue-industrial mb-4">
            ⭐ Productos Destacados para Vos
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {oportunidades.productos_destacados.map((producto, idx) => (
              <Card key={idx} className="hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <Badge variant="warning" className="mb-2">
                      {producto.familia}
                    </Badge>
                    <h3 className="font-semibold text-blue-industrial">
                      {producto.codigo}
                    </h3>
                    <p className="text-sm text-gray-text mt-1">
                      {producto.nombre}
                    </p>
                  </div>
                  <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-text">Precio:</span>
                    <span className="text-xl font-bold text-orange-mechanic">
                      {formatCurrency(producto.precio)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-text">Margen:</span>
                    <span className="font-semibold text-green-progress">
                      {producto.margen}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-text">Rotación:</span>
                    <span className={`font-semibold ${getRotacionColor(producto.rotacion)}`}>
                      {producto.rotacion}
                    </span>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-medium">
                  <p className="text-xs text-gray-text flex items-center gap-1">
                    <TrendingUp size={14} className="text-orange-mechanic" />
                    {producto.razon}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* CTA Section */}
      <Card className="bg-gradient-to-r from-blue-50 to-teal-50 border-2 border-blue-200">
        <div className="text-center">
          <h3 className="text-xl font-bold text-blue-industrial mb-2">
            ¿Querés saber más sobre estas oportunidades?
          </h3>
          <p className="text-gray-text mb-4">
            Contactá a tu asesor comercial para obtener más información y condiciones especiales
          </p>
          <Button variant="primary" className="w-full md:w-auto">
            Contactar Asesor
          </Button>
        </div>
      </Card>

      {/* Navegación */}
      <Card className="bg-gray-light">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
          <Button
            variant="outline"
            onClick={() => navigate('/portfolio')}
            className="w-full md:w-auto"
          >
            ← Anterior: Portfolio
          </Button>

          <Button
            variant="primary"
            onClick={() => navigate('/planes')}
            className="w-full md:w-auto"
          >
            Siguiente: Planes →
          </Button>
        </div>

        <p className="text-center text-xs text-gray-text mt-4">
          Paso 3 de 4 • Oportunidades
        </p>
      </Card>
    </div>
  );
};

export default OpportunitiesPage;
