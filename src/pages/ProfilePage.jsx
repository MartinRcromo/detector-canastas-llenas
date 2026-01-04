import React from 'react';
import { DollarSign, Package, ShoppingBag, Layers, TrendingUp, Calendar } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import Card from '../components/Card';
import Badge from '../components/Badge';
import { formatCUIT } from '../utils/formatters';

// DATOS MOCK HARDCODEADOS
const MOCK_PROFILE = {
  razon_social: 'DISTRIBUIDORA NORTE SA',
  cuit: '20301234567',
  cliente_id: '1001',
  cluster: 'A1',
  clasificacion: 'Activo Plus',
  total_anual: 2_500_000,
  total_unidades: 15000,
  cant_pedidos: 120,
  subrubros_activos: 8,
  periodo_analisis: '2024-01',
};

const ProfilePage = () => {
  const getClassificationColor = (clasificacion) => {
    const colors = {
      'Estratégico Premium': 'bg-purple-100 text-purple-800 border-purple-300',
      'Estratégico': 'bg-blue-100 text-blue-800 border-blue-300',
      'Activo Plus': 'bg-green-100 text-green-800 border-green-300',
      'Activo': 'bg-teal-100 text-teal-800 border-teal-300',
      'Desarrollo': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    };
    return colors[clasificacion] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-blue-industrial mb-2">
              {MOCK_PROFILE.razon_social}
            </h1>
            <div className="flex flex-wrap gap-3 items-center text-sm text-gray-text">
              <span>CUIT: {formatCUIT(MOCK_PROFILE.cuit)}</span>
              <span className="text-gray-medium">•</span>
              <span>ID: {MOCK_PROFILE.cliente_id}</span>
              <span className="text-gray-medium">•</span>
              <span>Cluster: {MOCK_PROFILE.cluster}</span>
            </div>
          </div>
          <div className="mt-4 md:mt-0">
            <Badge
              variant="success"
              className={`${getClassificationColor(MOCK_PROFILE.clasificacion)} text-lg px-4 py-2 border-2`}
            >
              {MOCK_PROFILE.clasificacion}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          label="Facturación Anual"
          value={MOCK_PROFILE.total_anual}
          type="currency"
          icon={DollarSign}
        />
        <MetricCard
          label="Unidades Vendidas"
          value={MOCK_PROFILE.total_unidades}
          type="number"
          icon={Package}
        />
        <MetricCard
          label="Cantidad de Pedidos"
          value={MOCK_PROFILE.cant_pedidos}
          type="number"
          icon={ShoppingBag}
        />
        <MetricCard
          label="Subrubros Activos"
          value={MOCK_PROFILE.subrubros_activos}
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
                  {MOCK_PROFILE.clasificacion}
                </h4>
                <p className="text-sm text-gray-text">
                  Cliente activo con potencial de crecimiento, facturación entre $1M y $3M anuales.
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
                  Datos del período: {MOCK_PROFILE.periodo_analisis}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-orange-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-orange-mechanic">
                  {MOCK_PROFILE.subrubros_activos}
                </p>
                <p className="text-xs text-gray-text mt-1">Categorías Activas</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <p className="text-2xl font-bold text-blue-industrial">
                  21K
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

      {/* Resumen de Compras */}
      <Card title="Resumen de Compras por Categoría">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-medium">
                <th className="text-left py-3 px-4 font-semibold text-blue-industrial">Categoría</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">Importe</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">Unidades</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">Pedidos</th>
                <th className="text-right py-3 px-4 font-semibold text-blue-industrial">% Total</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-medium hover:bg-gray-light">
                <td className="py-3 px-4 font-medium">FRENOS</td>
                <td className="py-3 px-4 text-right">$850.000</td>
                <td className="py-3 px-4 text-right">4.500</td>
                <td className="py-3 px-4 text-right">45</td>
                <td className="py-3 px-4 text-right">
                  <Badge variant="info">34%</Badge>
                </td>
              </tr>
              <tr className="border-b border-gray-medium hover:bg-gray-light">
                <td className="py-3 px-4 font-medium">SUSPENSIÓN</td>
                <td className="py-3 px-4 text-right">$650.000</td>
                <td className="py-3 px-4 text-right">3.200</td>
                <td className="py-3 px-4 text-right">38</td>
                <td className="py-3 px-4 text-right">
                  <Badge variant="info">26%</Badge>
                </td>
              </tr>
              <tr className="border-b border-gray-medium hover:bg-gray-light">
                <td className="py-3 px-4 font-medium">MOTOR</td>
                <td className="py-3 px-4 text-right">$550.000</td>
                <td className="py-3 px-4 text-right">2.800</td>
                <td className="py-3 px-4 text-right">32</td>
                <td className="py-3 px-4 text-right">
                  <Badge variant="info">22%</Badge>
                </td>
              </tr>
              <tr className="border-b border-gray-medium hover:bg-gray-light">
                <td className="py-3 px-4 font-medium">ELÉCTRICO</td>
                <td className="py-3 px-4 text-right">$450.000</td>
                <td className="py-3 px-4 text-right">4.500</td>
                <td className="py-3 px-4 text-right">28</td>
                <td className="py-3 px-4 text-right">
                  <Badge variant="info">18%</Badge>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default ProfilePage;
