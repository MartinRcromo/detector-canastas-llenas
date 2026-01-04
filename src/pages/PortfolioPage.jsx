import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp, Search } from 'lucide-react';
import Card from '../components/Card';
import ProgressBar from '../components/ProgressBar';
import Button from '../components/Button';
import FamiliaCard from '../components/FamiliaCard';
import FamiliaConfirmadaItem from '../components/FamiliaConfirmadaItem';

// DATOS MOCK - Familias ya confirmadas
const FAMILIAS_CONFIRMADAS = [
  { id: 1, nombre: "Filtros", subfamilias: "(aire, aceite, combustible)", confirmada: true },
  { id: 2, nombre: "Frenos", subfamilias: "(pastillas, discos, tambores)", confirmada: true },
  { id: 3, nombre: "Aceites y lubricantes", subfamilias: "", confirmada: true },
  { id: 4, nombre: "Iluminación", subfamilias: "(lámparas, faros)", confirmada: true },
  { id: 5, nombre: "Suspensión", subfamilias: "(amortiguadores, resortes)", confirmada: true },
];

// DATOS MOCK - Familias disponibles para agregar
const FAMILIAS_DISPONIBLES = [
  { id: 6, nombre: "Transmisión", icono: "Cog" },
  { id: 7, nombre: "Embrague", icono: "CircleDot" },
  { id: 8, nombre: "Refrigeración", icono: "Droplet" },
  { id: 9, nombre: "Baterías", icono: "Battery" },
  { id: 10, nombre: "Escapes", icono: "Wind" },
  { id: 11, nombre: "Distribución", icono: "Activity" },
  { id: 12, nombre: "Encendido", icono: "Zap" },
  { id: 13, nombre: "Eléctrico", icono: "Plug" },
  { id: 14, nombre: "Limpiaparabrisas", icono: "Droplets" },
  { id: 15, nombre: "Dirección", icono: "Navigation" },
  { id: 16, nombre: "Juntas", icono: "Circle" },
  { id: 17, nombre: "Retenes", icono: "Disc" },
];

const TOTAL_FAMILIAS = 20;

const PortfolioPage = () => {
  const navigate = useNavigate();
  const [familiasSeleccionadas, setFamiliasSeleccionadas] = useState([]);
  const [mostrarAyuda, setMostrarAyuda] = useState(false);
  const [busqueda, setBusqueda] = useState('');

  // Calcular progreso
  const familiasActuales = FAMILIAS_CONFIRMADAS.length + familiasSeleccionadas.length;
  const porcentajeCompletado = Math.round((familiasActuales / TOTAL_FAMILIAS) * 100);

  const toggleFamilia = (familiaId) => {
    if (familiasSeleccionadas.includes(familiaId)) {
      setFamiliasSeleccionadas(prev => prev.filter(id => id !== familiaId));
    } else {
      setFamiliasSeleccionadas(prev => [...prev, familiaId]);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Contextual */}
      <div>
        <h1 className="text-3xl font-bold text-blue-industrial mb-2">
          🛠️ Completá tu Portfolio
        </h1>
        <p className="text-gray-text">
          Confirmá qué familias manejás hoy y agregá las que faltan. Esto nos ayuda a mostrarte solo lo relevante.
        </p>
      </div>

      {/* Sección 1: Barra de Progreso del Portfolio */}
      <Card className="bg-gradient-to-r from-green-50 to-teal-50 border-2 border-green-200">
        <div className="text-center mb-4">
          <h3 className="text-lg font-semibold text-blue-industrial mb-1">
            Tu progreso de portfolio
          </h3>
          <p className="text-4xl font-bold text-green-progress mb-4">
            {familiasActuales} de {TOTAL_FAMILIAS} familias básicas
          </p>
        </div>
        <ProgressBar
          current={familiasActuales}
          target={TOTAL_FAMILIAS}
          showPercentage={true}
        />
      </Card>

      {/* Sección 2: Familias Confirmadas */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-2">
          ✓ Familias que ya manejás
        </h2>
        <p className="text-sm text-gray-text mb-4">
          Estas las detectamos según tus compras recientes
        </p>

        <Card>
          <div className="divide-y divide-gray-medium">
            {FAMILIAS_CONFIRMADAS.map((familia) => (
              <FamiliaConfirmadaItem
                key={familia.id}
                nombre={familia.nombre}
                subfamilias={familia.subfamilias}
              />
            ))}
          </div>
          <button className="mt-4 text-blue-industrial hover:text-orange-mechanic font-medium text-sm transition-colors">
            + Ver todas las confirmadas (7)
          </button>
        </Card>
      </div>

      {/* Sección 3: Agregá Familias */}
      <div>
        <h2 className="text-2xl font-bold text-blue-industrial mb-2">
          ➕ Agregá otras familias que vendés
        </h2>
        <p className="text-gray-text mb-6">
          Seleccioná todas las que apliquen a tu negocio
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {FAMILIAS_DISPONIBLES.map((familia) => (
            <FamiliaCard
              key={familia.id}
              familia={familia}
              isSelected={familiasSeleccionadas.includes(familia.id)}
              onClick={() => toggleFamilia(familia.id)}
            />
          ))}
        </div>

        <div className="mt-6 text-center">
          <button className="text-blue-industrial hover:text-orange-mechanic font-medium transition-colors">
            Cargar más familias ↓
          </button>
        </div>
      </div>

      {/* Sección 4: Buscador */}
      <Card>
        <h3 className="text-lg font-semibold text-blue-industrial mb-4">
          🔍 ¿No encontrás una familia?
        </h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-text" size={20} />
          <input
            type="text"
            placeholder="🔎 Buscá por nombre..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full h-12 pl-10 pr-4 border-2 border-gray-medium rounded-lg
                     focus:outline-none focus:border-blue-industrial transition-colors"
          />
        </div>
        <p className="text-sm text-gray-text mt-2">
          Ejemplos: "cilindro", "pastilla", "sensor"
        </p>
      </Card>

      {/* Sección 5: Ayuda Contextual */}
      <Card>
        <button
          onClick={() => setMostrarAyuda(!mostrarAyuda)}
          className="w-full flex items-center justify-between text-left group"
        >
          <span className="font-medium text-gray-graphite group-hover:text-blue-industrial transition-colors">
            💬 ¿Por qué necesitamos esta info?
          </span>
          {mostrarAyuda ? (
            <ChevronUp className="text-gray-text group-hover:text-blue-industrial transition-colors" />
          ) : (
            <ChevronDown className="text-gray-text group-hover:text-blue-industrial transition-colors" />
          )}
        </button>

        {mostrarAyuda && (
          <div className="mt-4 p-4 bg-gray-light rounded-lg space-y-2 animate-fade-in">
            <p className="text-gray-text">Conocer tu portfolio nos permite:</p>
            <ul className="space-y-2 ml-2">
              <li className="flex items-start gap-2 text-gray-text">
                <span className="text-green-progress mt-1">✓</span>
                <span>Mostrarte solo oportunidades relevantes</span>
              </li>
              <li className="flex items-start gap-2 text-gray-text">
                <span className="text-green-progress mt-1">✓</span>
                <span>No ofrecerte familias que ya manejás</span>
              </li>
              <li className="flex items-start gap-2 text-gray-text">
                <span className="text-green-progress mt-1">✓</span>
                <span>Sugerirte productos complementarios</span>
              </li>
              <li className="flex items-start gap-2 text-gray-text">
                <span className="text-green-progress mt-1">✓</span>
                <span>Compararte con repuestos de perfil similar</span>
              </li>
            </ul>
            <p className="text-sm text-gray-text mt-4 italic">
              No es obligatorio completar el 100%, pero cuanto más preciso sea,
              mejores recomendaciones vas a recibir.
            </p>
          </div>
        )}
      </Card>

      {/* Navegación Footer */}
      <Card className="bg-gray-light">
        <div className="text-center mb-6">
          <p className="text-gray-text mb-1">
            Podés continuar ahora o volver más tarde.
          </p>
          <p className="text-sm text-gray-text">
            Tu progreso se guarda automáticamente.
          </p>
        </div>

        <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
          <Button
            variant="outline"
            onClick={() => navigate('/perfil')}
            className="w-full md:w-auto"
          >
            ← Anterior: Perfil
          </Button>

          <Button
            variant="primary"
            onClick={() => navigate('/oportunidades')}
            className="w-full md:w-auto"
          >
            Siguiente: Oportunidades →
          </Button>
        </div>

        <p className="text-center text-xs text-gray-text mt-4">
          Paso 2 de 4 • Portfolio: {porcentajeCompletado}% completado
        </p>
      </Card>
    </div>
  );
};

export default PortfolioPage;
