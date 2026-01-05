import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, TrendingUp, Star, ChevronRight, ChevronDown, ChevronUp, ShoppingCart } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
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
  const { data: oportunidades, loading, error } = useApi(() => api.getOportunidades(cuit), [cuit]);

  const [familiaExpandida, setFamiliaExpandida] = useState(null);

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

                {/* Productos de la familia (expandible) */}
                {familiaExpandida === opp.id && opp.productos && opp.productos.length > 0 && (
                  <div className="mt-4 pt-4 border-t-2 border-gray-light animate-fade-in">
                    <h4 className="font-semibold text-gray-graphite mb-3">
                      Productos Sugeridos:
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {opp.productos.map((producto, idx) => (
                        <div
                          key={idx}
                          className="bg-gray-light rounded-lg p-4 hover:bg-orange-50 transition-colors"
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
