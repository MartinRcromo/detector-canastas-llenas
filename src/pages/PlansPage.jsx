import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, Check, Lock, TrendingUp, Zap, Users, Gift } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import ProgressBar from '../components/ProgressBar';
import { formatCurrency } from '../utils/formatters';

// DATOS MOCK - Cliente actual
const CLIENTE_ACTUAL = {
  facturacion_anual: 2_500_000,
  tier_actual: "Silver"
};

// DATOS MOCK - Definición de tiers
const TIERS = [
  {
    nombre: "Bronze",
    color: "from-orange-100 to-yellow-100",
    borderColor: "border-orange-300",
    iconColor: "text-orange-600",
    rango: "< $1M anual",
    objetivo: 1_000_000,
    descuento: "5%",
    beneficios: [
      "Descuento base 5%",
      "Asesor comercial asignado",
      "Portal de análisis comercial",
      "Acceso a catálogo completo"
    ]
  },
  {
    nombre: "Silver",
    color: "from-gray-200 to-gray-300",
    borderColor: "border-gray-400",
    iconColor: "text-gray-600",
    rango: "$1M - $3M anual",
    objetivo: 3_000_000,
    descuento: "5-7%",
    beneficios: [
      "Todo lo de Bronze",
      "Flete promocional (pedidos >$100k)",
      "Alertas de stock crítico",
      "Reportes mensuales personalizados"
    ]
  },
  {
    nombre: "Gold",
    color: "from-yellow-200 to-yellow-300",
    borderColor: "border-yellow-400",
    iconColor: "text-yellow-600",
    rango: "$3M - $6M anual",
    objetivo: 6_000_000,
    descuento: "7-10%",
    beneficios: [
      "Todo lo de Silver",
      "Plazo de pago 30 días",
      "Co-marketing digital",
      "Prioridad en atención técnica",
      "Material de marketing personalizado"
    ]
  },
  {
    nombre: "Platinum",
    color: "from-purple-200 to-pink-200",
    borderColor: "border-purple-400",
    iconColor: "text-purple-600",
    rango: ">$6M anual",
    objetivo: 10_000_000,
    descuento: "10-15%",
    beneficios: [
      "Todo lo de Gold",
      "Capacitación técnica trimestral",
      "Account Manager exclusivo",
      "Lanzamientos anticipados",
      "Condiciones especiales personalizadas"
    ]
  }
];

const PlansPage = () => {
  const navigate = useNavigate();
  const [tierSeleccionado, setTierSeleccionado] = useState(null);

  const tierActualIndex = TIERS.findIndex(t => t.nombre === CLIENTE_ACTUAL.tier_actual);
  const tierActual = TIERS[tierActualIndex];
  const siguienteTier = tierActualIndex < TIERS.length - 1 ? TIERS[tierActualIndex + 1] : null;

  const progresoActual = CLIENTE_ACTUAL.facturacion_anual;
  const objetivoSiguiente = siguienteTier ? siguienteTier.objetivo : tierActual.objetivo;
  const brechaSiguiente = siguienteTier ? objetivoSiguiente - progresoActual : 0;

  const isTierDesbloqueado = (tier) => {
    return TIERS.indexOf(tier) <= tierActualIndex;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-blue-industrial mb-2">
          🏆 Planes de Activación Comercial
        </h1>
        <p className="text-gray-text">
          Descubrí los beneficios de cada nivel y cómo alcanzar el siguiente tier
        </p>
      </div>

      {/* Tier Actual Card */}
      <Card className={`bg-gradient-to-r ${tierActual.color} border-2 ${tierActual.borderColor}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-md">
              <Award className={`w-8 h-8 ${tierActual.iconColor}`} />
            </div>
            <div>
              <p className="text-sm text-gray-text">Tu categoría actual</p>
              <h2 className="text-2xl font-bold text-blue-industrial">{tierActual.nombre}</h2>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-text">Facturación anual</p>
            <p className="text-2xl font-bold text-blue-industrial">
              {formatCurrency(CLIENTE_ACTUAL.facturacion_anual)}
            </p>
          </div>
        </div>

        {siguienteTier && (
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-gray-graphite">
                Progreso hacia {siguienteTier.nombre}
              </p>
              <p className="text-sm font-semibold text-blue-industrial">
                Faltan {formatCurrency(brechaSiguiente)}
              </p>
            </div>
            <ProgressBar
              current={progresoActual}
              target={objetivoSiguiente}
              showPercentage={true}
            />
          </div>
        )}
      </Card>

      {/* Beneficios Actuales */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-4">
          ✓ Tus Beneficios Actuales ({tierActual.nombre})
        </h2>
        <Card>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {tierActual.beneficios.map((beneficio, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <Check className="w-5 h-5 text-green-progress flex-shrink-0 mt-0.5" />
                <span className="text-sm text-green-900">{beneficio}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Próximos Beneficios */}
      {siguienteTier && (
        <div>
          <h2 className="text-2xl font-bold text-blue-industrial mb-4">
            🎁 Desbloqueá estos beneficios con {siguienteTier.nombre}
          </h2>
          <Card className="bg-orange-50 border-2 border-orange-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {siguienteTier.beneficios.filter(b => !tierActual.beneficios.includes(b)).map((beneficio, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3 bg-white rounded-lg border border-orange-200">
                  <Lock className="w-5 h-5 text-orange-mechanic flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-graphite">{beneficio}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-start gap-2">
                <Zap className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-yellow-900 mb-1">
                    ¡Estás cerca de {siguienteTier.nombre}!
                  </p>
                  <p className="text-sm text-yellow-800">
                    Con {formatCurrency(brechaSiguiente)} más en facturación anual,
                    desbloqueás {siguienteTier.beneficios.length - tierActual.beneficios.length} beneficios adicionales.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Comparación de Todos los Planes */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-4">
          📊 Compará Todos los Planes
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {TIERS.map((tier, idx) => {
            const isActual = tier.nombre === CLIENTE_ACTUAL.tier_actual;
            const isDesbloqueado = isTierDesbloqueado(tier);

            return (
              <Card
                key={tier.nombre}
                className={`
                  relative cursor-pointer transition-all
                  ${isActual ? `bg-gradient-to-b ${tier.color} border-2 ${tier.borderColor} shadow-lg` : ''}
                  ${!isActual && isDesbloqueado ? 'opacity-75' : ''}
                  ${!isDesbloqueado ? 'opacity-60' : ''}
                  ${tierSeleccionado === tier.nombre ? 'ring-2 ring-blue-industrial' : ''}
                `}
                onClick={() => setTierSeleccionado(tier.nombre)}
              >
                {isActual && (
                  <div className="absolute top-2 right-2">
                    <Badge variant="success" className="text-xs">Actual</Badge>
                  </div>
                )}

                <div className="text-center mb-4">
                  <div className={`w-16 h-16 mx-auto mb-3 bg-white rounded-full flex items-center justify-center shadow-md`}>
                    <Award className={`w-8 h-8 ${tier.iconColor}`} />
                  </div>
                  <h3 className="text-xl font-bold text-blue-industrial mb-1">{tier.nombre}</h3>
                  <p className="text-xs text-gray-text">{tier.rango}</p>
                </div>

                <div className="mb-4 p-3 bg-white rounded-lg">
                  <p className="text-xs text-gray-text text-center mb-1">Descuento</p>
                  <p className="text-2xl font-bold text-center text-orange-mechanic">{tier.descuento}</p>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-graphite mb-2">Beneficios incluidos:</p>
                  {tier.beneficios.slice(0, 3).map((beneficio, idx) => (
                    <div key={idx} className="flex items-start gap-2">
                      <Check className="w-4 h-4 text-green-progress flex-shrink-0 mt-0.5" />
                      <span className="text-xs text-gray-text">{beneficio}</span>
                    </div>
                  ))}
                  {tier.beneficios.length > 3 && (
                    <p className="text-xs text-gray-text italic">+{tier.beneficios.length - 3} más...</p>
                  )}
                </div>

                {!isDesbloqueado && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-gray-text">
                    <Lock className="w-4 h-4" />
                    <span className="text-xs">Bloqueado</span>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* Cómo Alcanzar el Siguiente Nivel */}
      {siguienteTier && (
        <Card className="bg-blue-50 border-2 border-blue-200">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-industrial rounded-full flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-blue-industrial mb-3">
                Cómo llegar a {siguienteTier.nombre}
              </h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-orange-mechanic rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                    1
                  </div>
                  <div>
                    <p className="font-medium text-gray-graphite">Aprovechá las oportunidades de cross-selling</p>
                    <p className="text-sm text-gray-text">
                      Agregando las 4 familias sugeridas, podés sumar {formatCurrency(640000)} mensuales
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-orange-mechanic rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                    2
                  </div>
                  <div>
                    <p className="font-medium text-gray-graphite">Diversificá tu portfolio</p>
                    <p className="text-sm text-gray-text">
                      Completá al menos 15 de las 20 familias básicas para maximizar oportunidades
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-orange-mechanic rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold">
                    3
                  </div>
                  <div>
                    <p className="font-medium text-gray-graphite">Hablá con tu asesor comercial</p>
                    <p className="text-sm text-gray-text">
                      Te ayudamos a armar un plan personalizado para alcanzar tus objetivos
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <Button variant="primary">
                  <Users className="w-4 h-4 mr-2" />
                  Contactar a mi asesor
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Already at Max Tier */}
      {!siguienteTier && (
        <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-200">
          <div className="text-center py-6">
            <Award className="w-16 h-16 text-purple-600 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-purple-900 mb-2">
              ¡Felicitaciones!
            </h3>
            <p className="text-gray-text max-w-2xl mx-auto mb-4">
              Alcanzaste el nivel {tierActual.nombre}, la categoría más alta de nuestro programa.
              Disfrutá de todos los beneficios exclusivos y seguí creciendo con nosotros.
            </p>
            <Button variant="primary">
              <Gift className="w-4 h-4 mr-2" />
              Ver beneficios exclusivos
            </Button>
          </div>
        </Card>
      )}

      {/* Navegación Footer */}
      <Card className="bg-gray-light">
        <div className="text-center mb-6">
          <p className="text-gray-text mb-1">
            ¿Tenés preguntas sobre los planes?
          </p>
          <p className="text-sm text-gray-text">
            Nuestro equipo está para ayudarte a elegir el mejor camino
          </p>
        </div>

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
            Volver al Inicio
          </Button>
        </div>

        <p className="text-center text-xs text-gray-text mt-4">
          Paso 4 de 4 • Plan actual: {tierActual.nombre}
        </p>
      </Card>
    </div>
  );
};

export default PlansPage;
