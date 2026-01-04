import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lightbulb, TrendingUp, Star, ChevronRight, ShoppingCart } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import { formatCurrency, formatNumber } from '../utils/formatters';

// DATOS MOCK - Oportunidades por familia
const OPORTUNIDADES_FAMILIAS = [
  {
    id: 1,
    familia: "Transmisión",
    razon: "Clientes similares compran",
    potencial_mensual: 185000,
    productos_sugeridos: 8,
    prioridad: "alta",
    productos: [
      { codigo: "TX-450", nombre: "Kit Embrague Premium", precio: 45000, demanda: "Alta" },
      { codigo: "TX-120", nombre: "Volante Motor Bimasa", precio: 68000, demanda: "Media" },
      { codigo: "TX-890", nombre: "Disco Embrague Reforzado", precio: 32000, demanda: "Alta" },
    ]
  },
  {
    id: 2,
    familia: "Refrigeración",
    razon: "Complementa tu portfolio actual",
    potencial_mensual: 142000,
    productos_sugeridos: 12,
    prioridad: "alta",
    productos: [
      { codigo: "RF-301", nombre: "Radiador Aluminio", precio: 52000, demanda: "Alta" },
      { codigo: "RF-102", nombre: "Bomba Agua Premium", precio: 28000, demanda: "Media" },
      { codigo: "RF-550", nombre: "Termostato Universal", precio: 8500, demanda: "Alta" },
    ]
  },
  {
    id: 3,
    familia: "Distribución",
    razon: "Alta rotación en tu zona",
    potencial_mensual: 98000,
    productos_sugeridos: 6,
    prioridad: "media",
    productos: [
      { codigo: "DT-780", nombre: "Kit Distribución Completo", precio: 85000, demanda: "Alta" },
      { codigo: "DT-234", nombre: "Correa Distribución", precio: 18000, demanda: "Media" },
    ]
  },
  {
    id: 4,
    familia: "Baterías",
    razon: "Oportunidad estacional",
    potencial_mensual: 215000,
    productos_sugeridos: 5,
    prioridad: "media",
    productos: [
      { codigo: "BT-120", nombre: "Batería 12V 75Ah", precio: 62000, demanda: "Alta" },
      { codigo: "BT-450", nombre: "Batería AGM Premium", precio: 95000, demanda: "Media" },
    ]
  },
];

// DATOS MOCK - Productos destacados
const PRODUCTOS_DESTACADOS = [
  {
    codigo: "FR-891",
    nombre: "Kit Frenos Cerámicos Premium",
    familia: "Frenos",
    precio: 78000,
    margen: 35,
    rotacion: "Muy Alta",
    razon: "Top ventas en tu segmento"
  },
  {
    codigo: "SU-456",
    nombre: "Amortiguador Gas Regulable",
    familia: "Suspensión",
    precio: 42000,
    margen: 28,
    rotacion: "Alta",
    razon: "Complementa tu portfolio"
  },
  {
    codigo: "IL-223",
    nombre: "Kit LED H7 6000K",
    familia: "Iluminación",
    precio: 18500,
    margen: 42,
    rotacion: "Alta",
    razon: "Tendencia creciente"
  },
];

const OpportunitiesPage = () => {
  const navigate = useNavigate();
  const [familiaExpandida, setFamiliaExpandida] = useState(null);

  const toggleFamilia = (familiaId) => {
    setFamiliaExpandida(familiaExpandida === familiaId ? null : familiaId);
  };

  const getPrioridadColor = (prioridad) => {
    return prioridad === 'alta'
      ? 'bg-orange-100 text-orange-800 border-orange-300'
      : 'bg-blue-100 text-blue-800 border-blue-300';
  };

  const totalPotencial = OPORTUNIDADES_FAMILIAS.reduce((sum, opp) => sum + opp.potencial_mensual, 0);

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
              {formatCurrency(totalPotencial)}
            </p>
            <p className="text-sm text-gray-text">
              Basado en {OPORTUNIDADES_FAMILIAS.length} familias recomendadas
            </p>
          </div>
          <div className="hidden md:block w-20 h-20 bg-orange-mechanic rounded-full flex items-center justify-center">
            <Lightbulb className="w-10 h-10 text-white" />
          </div>
        </div>
      </Card>

      {/* Familias Recomendadas */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-4">
          🎯 Nuevas Familias Recomendadas
        </h2>

        <div className="space-y-4">
          {OPORTUNIDADES_FAMILIAS.map((opp) => (
            <Card key={opp.id} className="hover:border-orange-mechanic border-2 border-transparent transition-all">
              <div
                className="cursor-pointer"
                onClick={() => toggleFamilia(opp.id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-blue-industrial">
                        {opp.familia}
                      </h3>
                      <Badge className={`${getPrioridadColor(opp.prioridad)} border`}>
                        Prioridad {opp.prioridad}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-text mb-2">
                      <TrendingUp className="inline w-4 h-4 mr-1" />
                      {opp.razon}
                    </p>
                  </div>
                  <ChevronRight
                    className={`w-6 h-6 text-gray-text transition-transform ${
                      familiaExpandida === opp.id ? 'rotate-90' : ''
                    }`}
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="bg-gray-light rounded-lg p-3">
                    <p className="text-xs text-gray-text">Potencial mensual</p>
                    <p className="text-lg font-bold text-green-progress">
                      {formatCurrency(opp.potencial_mensual)}
                    </p>
                  </div>
                  <div className="bg-gray-light rounded-lg p-3">
                    <p className="text-xs text-gray-text">Productos sugeridos</p>
                    <p className="text-lg font-bold text-blue-industrial">
                      {opp.productos_sugeridos}
                    </p>
                  </div>
                  <div className="bg-gray-light rounded-lg p-3 col-span-2 md:col-span-1">
                    <p className="text-xs text-gray-text">Tiempo estimado setup</p>
                    <p className="text-lg font-bold text-gray-graphite">2-3 semanas</p>
                  </div>
                </div>
              </div>

              {/* Productos expandidos */}
              {familiaExpandida === opp.id && (
                <div className="mt-4 pt-4 border-t border-gray-medium animate-fade-in">
                  <h4 className="font-semibold text-blue-industrial mb-3">
                    Productos Top en {opp.familia}:
                  </h4>
                  <div className="space-y-2">
                    {opp.productos.map((prod, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gray-light rounded-lg hover:bg-blue-50 transition-colors"
                      >
                        <div className="flex-1">
                          <p className="font-medium text-gray-graphite">{prod.nombre}</p>
                          <p className="text-xs text-gray-text">SKU: {prod.codigo}</p>
                        </div>
                        <div className="text-right mr-4">
                          <p className="font-semibold text-green-progress">
                            {formatCurrency(prod.precio)}
                          </p>
                          <Badge variant="info" className="text-xs">
                            {prod.demanda}
                          </Badge>
                        </div>
                        <Button variant="outline" className="py-1 px-3 text-sm">
                          Ver más
                        </Button>
                      </div>
                    ))}
                  </div>
                  <button className="mt-3 text-orange-mechanic hover:text-orange-600 font-medium text-sm">
                    Ver todos los productos de {opp.familia} →
                  </button>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Productos Destacados */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-2">
          ⭐ Productos Destacados
        </h2>
        <p className="text-gray-text mb-4">
          SKUs específicos con alto potencial para tu negocio
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PRODUCTOS_DESTACADOS.map((prod, idx) => (
            <Card key={idx} className="hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <Badge variant="orange" className="text-xs">
                  {prod.familia}
                </Badge>
                <Star className="w-5 h-5 text-yellow-alert fill-current" />
              </div>

              <h3 className="font-semibold text-gray-graphite mb-2">{prod.nombre}</h3>
              <p className="text-xs text-gray-text mb-3">SKU: {prod.codigo}</p>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-text">Precio sugerido:</span>
                  <span className="font-semibold text-green-progress">
                    {formatCurrency(prod.precio)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-text">Margen esperado:</span>
                  <span className="font-semibold text-blue-industrial">{prod.margen}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-text">Rotación:</span>
                  <Badge variant="success" className="text-xs">{prod.rotacion}</Badge>
                </div>
              </div>

              <div className="bg-orange-50 rounded-lg p-2 mb-3">
                <p className="text-xs text-orange-900">
                  💡 {prod.razon}
                </p>
              </div>

              <Button variant="primary" className="w-full py-2">
                <ShoppingCart className="w-4 h-4 mr-2" />
                Agregar al pedido
              </Button>
            </Card>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <Card className="bg-blue-50 border-2 border-blue-200">
        <div className="text-center">
          <h3 className="text-xl font-bold text-blue-industrial mb-2">
            ¿Querés más detalles sobre estas oportunidades?
          </h3>
          <p className="text-gray-text mb-4">
            Nuestro equipo comercial puede ayudarte a armar un plan personalizado
          </p>
          <Button variant="primary">
            Hablar con un asesor
          </Button>
        </div>
      </Card>

      {/* Navegación Footer */}
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
            Siguiente: Ver Planes →
          </Button>
        </div>

        <p className="text-center text-xs text-gray-text mt-4">
          Paso 3 de 4 • Oportunidades identificadas: {OPORTUNIDADES_FAMILIAS.length}
        </p>
      </Card>
    </div>
  );
};

export default OpportunitiesPage;
