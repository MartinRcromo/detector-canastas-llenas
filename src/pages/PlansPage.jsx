import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Check, Lock, TrendingUp, Zap, Users, Gift } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCurrency } from '../utils/formatters';

const PlansPage = () => {
  const navigate = useNavigate();
  const { cuit } = useCliente();
  const { data: planes, loading, error } = useApi(() => api.getPlanes(cuit), [cuit]);

  const [tierSeleccionado, setTierSeleccionado] = useState(null);

  if (loading) {
    return <Loading message="Cargando planes de activación..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Error al cargar planes"
        message={error}
      />
    );
  }

  if (!planes) {
    return null;
  }

  const tierActualIndex = planes.tiers.findIndex(t => t.nombre === planes.tier_actual);
  const tierActual = planes.tiers[tierActualIndex];
  const siguienteTier = tierActualIndex < planes.tiers.length - 1 ? planes.tiers[tierActualIndex + 1] : null;

  const isTierDesbloqueado = (tier) => {
    return planes.tiers.indexOf(tier) <= tierActualIndex;
  };

  const getTierIcon = (nombre) => {
    const icons = {
      'Bronze': Award,
      'Silver': Zap,
      'Gold': TrendingUp,
      'Platinum': Gift,
    };
    return icons[nombre] || Award;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-blue-industrial mb-2">
          🎯 Planes de Activación Comercial
        </h1>
        <p className="text-gray-text">
          Descubrí los beneficios de cada nivel y cómo alcanzar el siguiente tier
        </p>
      </div>

      {/* Tier Actual y Progreso */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tier Actual */}
        <Card className={`bg-gradient-to-r ${tierActual.color} border-2 ${tierActual.borderColor}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-text mb-1">Tu nivel actual</p>
              <h2 className="text-3xl font-bold text-blue-industrial">
                {planes.tier_actual}
              </h2>
            </div>
            <div className={`w-16 h-16 rounded-full bg-white flex items-center justify-center ${tierActual.iconColor}`}>
              {React.createElement(getTierIcon(planes.tier_actual), { size: 32 })}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-text">Facturación anual:</span>
              <span className="font-semibold text-blue-industrial">
                {formatCurrency(planes.facturacion_anual)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-text">Descuento:</span>
              <span className="font-semibold text-green-progress">
                {tierActual.descuento}
              </span>
            </div>
          </div>
        </Card>

        {/* Progreso al Siguiente Tier */}
        {siguienteTier && (
          <Card className="bg-gradient-to-r from-green-50 to-teal-50 border-2 border-green-200">
            <div className="mb-4">
              <p className="text-sm text-gray-text mb-1">Próximo objetivo</p>
              <h3 className="text-2xl font-bold text-blue-industrial mb-2">
                Tier {planes.siguiente_tier}
              </h3>
              <p className="text-sm text-gray-text">
                Te faltan {formatCurrency(planes.brecha_siguiente || 0)} para alcanzarlo
              </p>
            </div>

            <ProgressBar
              current={planes.facturacion_anual}
              target={siguienteTier.objetivo}
              showPercentage={true}
              color="green"
            />

            <div className="mt-4 p-3 bg-white rounded-lg">
              <p className="text-xs text-gray-text mb-1">Beneficios que desbloquearás:</p>
              <ul className="space-y-1">
                {siguienteTier.beneficios.slice(1, 3).map((beneficio, idx) => (
                  <li key={idx} className="text-sm text-blue-industrial flex items-center gap-2">
                    <Lock size={12} className="text-gray-text" />
                    {beneficio}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        )}

        {/* Cliente ya en tier máximo */}
        {!siguienteTier && (
          <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200">
            <div className="text-center py-6">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-white flex items-center justify-center">
                <Award size={32} className="text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-blue-industrial mb-2">
                ¡Felicitaciones!
              </h3>
              <p className="text-gray-text">
                Ya alcanzaste el tier más alto. Seguí creciendo para mantener tus beneficios premium.
              </p>
            </div>
          </Card>
        )}
      </div>

      {/* Comparación de Tiers */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-4">
          📊 Compará todos los niveles
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {planes.tiers.map((tier, index) => {
            const TierIcon = getTierIcon(tier.nombre);
            const esActual = tier.nombre === planes.tier_actual;
            const estaDesbloqueado = isTierDesbloqueado(tier);

            return (
              <Card
                key={index}
                className={`
                  relative cursor-pointer transition-all
                  ${esActual ? `border-4 ${tier.borderColor} shadow-lg` : 'border-2 border-gray-medium'}
                  ${tierSeleccionado === tier.nombre ? 'ring-2 ring-blue-industrial' : ''}
                  hover:shadow-lg
                `}
                onClick={() => setTierSeleccionado(tierSeleccionado === tier.nombre ? null : tier.nombre)}
              >
                {esActual && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge variant="success" className="bg-green-500 text-white border-2 border-white">
                      Tu nivel actual
                    </Badge>
                  </div>
                )}

                {!estaDesbloqueado && (
                  <div className="absolute top-2 right-2">
                    <Lock size={20} className="text-gray-text" />
                  </div>
                )}

                <div className={`bg-gradient-to-r ${tier.color} rounded-lg p-4 mb-4`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-xl font-bold text-blue-industrial">
                      {tier.nombre}
                    </h3>
                    <TierIcon size={24} className={tier.iconColor} />
                  </div>
                  <p className="text-sm text-gray-text">{tier.rango}</p>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-text mb-1">Descuento</p>
                    <p className="text-2xl font-bold text-orange-mechanic">
                      {tier.descuento}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-text mb-2">Beneficios principales:</p>
                    <ul className="space-y-1.5">
                      {tier.beneficios.slice(0, 3).map((beneficio, idx) => (
                        <li
                          key={idx}
                          className={`text-xs flex items-start gap-2 ${
                            estaDesbloqueado ? 'text-blue-industrial' : 'text-gray-text'
                          }`}
                        >
                          {estaDesbloqueado ? (
                            <Check size={14} className="text-green-progress mt-0.5 flex-shrink-0" />
                          ) : (
                            <Lock size={14} className="text-gray-text mt-0.5 flex-shrink-0" />
                          )}
                          <span>{beneficio}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {tierSeleccionado === tier.nombre && tier.beneficios.length > 3 && (
                    <div className="pt-3 border-t border-gray-medium animate-fade-in">
                      <p className="text-xs text-gray-text mb-2">Beneficios adicionales:</p>
                      <ul className="space-y-1.5">
                        {tier.beneficios.slice(3).map((beneficio, idx) => (
                          <li
                            key={idx}
                            className={`text-xs flex items-start gap-2 ${
                              estaDesbloqueado ? 'text-blue-industrial' : 'text-gray-text'
                            }`}
                          >
                            {estaDesbloqueado ? (
                              <Check size={14} className="text-green-progress mt-0.5 flex-shrink-0" />
                            ) : (
                              <Lock size={14} className="text-gray-text mt-0.5 flex-shrink-0" />
                            )}
                            <span>{beneficio}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {!esActual && estaDesbloqueado && (
                  <div className="mt-4 pt-3 border-t border-gray-medium">
                    <Badge variant="success" className="w-full text-center bg-green-50 text-green-700">
                      ✓ Nivel completado
                    </Badge>
                  </div>
                )}

                {!estaDesbloqueado && index === tierActualIndex + 1 && (
                  <div className="mt-4 pt-3 border-t border-gray-medium">
                    <Button
                      variant="primary"
                      className="w-full text-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate('/oportunidades');
                      }}
                    >
                      Ver cómo alcanzarlo
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* CTA Final */}
      <Card className="bg-gradient-to-r from-blue-50 to-teal-50 border-2 border-blue-200">
        <div className="text-center">
          <Users className="w-12 h-12 mx-auto mb-4 text-blue-industrial" />
          <h3 className="text-xl font-bold text-blue-industrial mb-2">
            ¿Querés acelerar tu crecimiento?
          </h3>
          <p className="text-gray-text mb-4">
            Nuestro equipo comercial puede ayudarte a diseñar un plan personalizado
            para alcanzar el siguiente nivel
          </p>
          <Button variant="primary" className="w-full md:w-auto">
            Hablar con mi asesor
          </Button>
        </div>
      </Card>

      {/* Navegación */}
      <Card className="bg-gray-light">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
          <Button
            variant="outline"
            onClick={() => navigate('/oportunidades')}
            className="w-full md:w-auto"
          >
            ← Anterior: Oportunidades
          </Button>

          <Button
            variant="primary"
            onClick={() => navigate('/perfil')}
            className="w-full md:w-auto"
          >
            Volver al inicio
          </Button>
        </div>

        <p className="text-center text-xs text-gray-text mt-4">
          Paso 4 de 4 • Planes de Activación
        </p>
      </Card>
    </div>
  );
};

export default PlansPage;
