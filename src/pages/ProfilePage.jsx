import React from 'react';
import { DollarSign, Package, ShoppingBag, Layers, TrendingUp, Calendar } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import MetricCard from '../components/MetricCard';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { formatCUIT, formatCurrency } from '../utils/formatters';

const ProfilePage = () => {
  const { cuit } = useCliente();
  const { data: perfil, loading, error } = useApi(() => api.getPerfil(cuit), [cuit]);

  const getClassificationColor = (clasificacion) => {
    const colors = {
      'Estratégico Premium': 'bg-purple-100 text-purple-800 border-purple-300',
      'Estratégico': 'bg-blue-100 text-blue-800 border-blue-300',
      'Activo Plus': 'bg-green-100 text-green-800 border-green-300',
      'Activo': 'bg-teal-100 text-teal-800 border-teal-300',
      'En desarrollo': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'Nuevo': 'bg-gray-100 text-gray-800 border-gray-300',
    };
    return colors[clasificacion] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getClassificationDescription = (clasificacion) => {
    const descriptions = {
      'Activo Plus': 'Cliente activo con excelente performance, facturación mayor a $3M anuales.',
      'Activo': 'Cliente activo con buen potencial, facturación entre $1.5M y $3M anuales.',
      'En desarrollo': 'Cliente en crecimiento, facturación entre $500K y $1.5M anuales.',
      'Nuevo': 'Cliente nuevo con potencial de desarrollo.',
    };
    return descriptions[clasificacion] || 'Cliente del sistema.';
  };

  if (loading) {
    return <Loading message="Cargando perfil del cliente..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Error al cargar el perfil"
        message={error}
      />
    );
  }

  if (!perfil) {
    return null;
  }

  // Calcular ticket promedio
  const ticketPromedio = perfil.cantidad_pedidos > 0
    ? perfil.facturacion_anual / perfil.cantidad_pedidos
    : 0;

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-industrial mb-2">
              {perfil.nombre_empresa}
            </h1>
            <div className="flex flex-wrap gap-3 items-center text-sm text-gray-text">
              <span>CUIT: {formatCUIT(perfil.cuit)}</span>
            </div>
          </div>
          <div className="mt-4 md:mt-0">
            <Badge
              variant="success"
              className={`${getClassificationColor(perfil.clasificacion)} text-lg px-4 py-2 border-2`}
            >
              {perfil.clasificacion}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          label="Facturación Anual"
          value={perfil.facturacion_anual}
          type="currency"
          icon={DollarSign}
        />
        <MetricCard
          label="Unidades Compradas"
          value={perfil.unidades_compradas}
          type="number"
          icon={Package}
        />
        <MetricCard
          label="Cantidad de Pedidos"
          value={perfil.cantidad_pedidos}
          type="number"
          icon={ShoppingBag}
        />
        <MetricCard
          label="Subrubros Activos"
          value={perfil.subrubros_activos}
          type="number"
          icon={Layers}
        />
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Clasificación Comercial */}
        <Card title="Clasificación Comercial">
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center mr-4">
                <TrendingUp className="w-6 h-6 text-blue-industrial" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-blue-industrial mb-1">
                  {perfil.clasificacion}
                </h4>
                <p className="text-sm text-gray-text">
                  {getClassificationDescription(perfil.clasificacion)}
                </p>
              </div>
            </div>

            <div className="bg-gray-light rounded-lg p-4">
              <h5 className="font-medium text-gray-graphite mb-2">Características del perfil:</h5>
              <ul className="space-y-2 text-sm text-gray-text">
                <li className="flex items-center">
                  <span className="w-1.5 h-1.5 bg-orange-mechanic rounded-full mr-2"></span>
                  Descuentos por volumen
                </li>
                <li className="flex items-center">
                  <span className="w-1.5 h-1.5 bg-orange-mechanic rounded-full mr-2"></span>
                  Flete promocional
                </li>
                <li className="flex items-center">
                  <span className="w-1.5 h-1.5 bg-orange-mechanic rounded-full mr-2"></span>
                  Análisis de oportunidades
                </li>
                <li className="flex items-center">
                  <span className="w-1.5 h-1.5 bg-orange-mechanic rounded-full mr-2"></span>
                  Reportes mensuales
                </li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Análisis de Actividad */}
        <Card title="Análisis de Actividad">
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center mr-4">
                <Calendar className="w-6 h-6 text-green-progress" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-blue-industrial mb-1">
                  Período de Análisis
                </h4>
                <p className="text-sm text-gray-text">
                  Datos de los últimos 12 meses
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-orange-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-orange-mechanic">
                  {perfil.subrubros_activos}
                </p>
                <p className="text-xs text-gray-text mt-1">Categorías Activas</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-blue-industrial">
                  {formatCurrency(ticketPromedio)}
                </p>
                <p className="text-xs text-gray-text mt-1">Ticket Promedio</p>
              </div>
            </div>

            <div className="bg-gray-light rounded-lg p-4">
              <p className="text-sm text-gray-text">
                <span className="font-medium text-blue-industrial">Próximos pasos:</span> Explore las
                oportunidades de cross-selling y descubra cómo aumentar su facturación activando nuevos
                subrubros y optimizando su portfolio actual.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Compras Recientes */}
      <Card title="Compras Recientes">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-medium">
                <th className="text-left py-3 px-4 font-semibold text-blue-industrial">Fecha</th>
                <th className="text-left py-3 px-4 font-semibold text-blue-industrial">Artículo</th>
                <th className="text-left py-3 px-4 font-semibold text-blue-industrial">Subrubro</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">Cantidad</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">Monto</th>
              </tr>
            </thead>
            <tbody>
              {perfil.compras_recientes && perfil.compras_recientes.length > 0 ? (
                perfil.compras_recientes.map((compra, idx) => (
                  <tr key={idx} className="border-b border-gray-medium hover:bg-gray-light">
                    <td className="py-3 px-4">{compra.fecha}</td>
                    <td className="py-3 px-4">
                      <div className="font-medium">{compra.codigo_articulo}</div>
                      <div className="text-xs text-gray-text">{compra.nombre_articulo}</div>
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="info">{compra.subrubro}</Badge>
                    </td>
                    <td className="py-3 px-4 text-right">{compra.cantidad}</td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(compra.monto)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-gray-text">
                    No hay compras recientes para mostrar
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ProfilePage;
