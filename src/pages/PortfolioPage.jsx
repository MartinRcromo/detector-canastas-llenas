import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronUp, Search } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import Card from '../components/Card';
import ProgressBar from '../components/ProgressBar';
import Button from '../components/Button';
import FamiliaCard from '../components/FamiliaCard';
import FamiliaConfirmadaItem from '../components/FamiliaConfirmadaItem';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';

const PortfolioPage = () => {
  const navigate = useNavigate();
  const { cuit } = useCliente();
  const { data: portfolio, loading, error } = useApi(() => api.getPortfolio(cuit), [cuit]);

  const [familiasSeleccionadas, setFamiliasSeleccionadas] = useState([]);
  const [mostrarAyuda, setMostrarAyuda] = useState(false);
  const [busqueda, setBusqueda] = useState('');

  if (loading) {
    return <Loading message="Cargando portfolio..." />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Error al cargar el portfolio"
        message={error}
      />
    );
  }

  if (!portfolio) {
    return null;
  }

  // Calcular progreso incluyendo las familias seleccionadas por el usuario
  const familiasActuales = portfolio.familias_confirmadas.length + familiasSeleccionadas.length;
  const porcentajeCompletado = Math.round((familiasActuales / portfolio.total_familias_posibles) * 100);

  const toggleFamilia = (familiaId) => {
    if (familiasSeleccionadas.includes(familiaId)) {
      setFamiliasSeleccionadas(prev => prev.filter(id => id !== familiaId));
    } else {
      setFamiliasSeleccionadas(prev => [...prev, familiaId]);
    }
  };

  // Filtrar familias disponibles por búsqueda
  const familiasDisponiblesFiltradas = busqueda
    ? portfolio.familias_disponibles.filter(f =>
        f.nombre.toLowerCase().includes(busqueda.toLowerCase())
      )
    : portfolio.familias_disponibles;

  return (
    <div className="space-y-8">
      {/* Header Contextual */}
      <div>
        <h1 className="text-3xl font-bold text-blue-industrial mb-2">
          Completá tu Portfolio
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
            {familiasActuales} de {portfolio.total_familias_posibles} familias básicas
          </p>
        </div>
        <ProgressBar
          current={familiasActuales}
          target={portfolio.total_familias_posibles}
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
          {portfolio.familias_confirmadas.length > 0 ? (
            <>
              <div className="divide-y divide-gray-medium">
                {portfolio.familias_confirmadas.map((familia) => (
                  <FamiliaConfirmadaItem
                    key={familia.id}
                    nombre={familia.nombre}
                    subfamilias={familia.subfamilias}
                  />
                ))}
              </div>
              {portfolio.familias_confirmadas.length > 5 && (
                <button className="mt-4 text-blue-industrial hover:text-orange-mechanic font-medium text-sm transition-colors">
                  + Ver todas las confirmadas ({portfolio.familias_confirmadas.length})
                </button>
              )}
            </>
          ) : (
            <div className="text-center py-8 text-gray-text">
              <p>No se detectaron familias confirmadas aún.</p>
              <p className="text-sm mt-2">Seleccioná las familias que manejás a continuación.</p>
            </div>
          )}
        </Card>
      </div>

      {/* Sección 3: Agregá Familias */}
      {portfolio.familias_disponibles.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-blue-industrial mb-2">
            ➕ Agregá otras familias que vendés
          </h2>
          <p className="text-gray-text mb-6">
            Seleccioná todas las que apliquen a tu negocio
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {familiasDisponiblesFiltradas.map((familia) => (
              <FamiliaCard
                key={familia.id}
                familia={familia}
                isSelected={familiasSeleccionadas.includes(familia.id)}
                onClick={() => toggleFamilia(familia.id)}
              />
            ))}
          </div>

          {familiasDisponiblesFiltradas.length === 0 && busqueda && (
            <div className="text-center py-8 text-gray-text">
              No se encontraron familias con "{busqueda}"
            </div>
          )}

          {familiasSeleccionadas.length > 0 && (
            <div className="mt-6 p-4 bg-green-50 border-2 border-green-200 rounded-lg">
              <p className="text-green-800 font-medium text-center">
                ✓ {familiasSeleccionadas.length} familia{familiasSeleccionadas.length > 1 ? 's' : ''} seleccionada{familiasSeleccionadas.length > 1 ? 's' : ''}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Sección 4: Buscador */}
      <Card>
        <h3 className="text-lg font-semibold text-blue-industrial mb-4">
          🔍 ¿No encontrás una familia?
        </h3>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-text" size={20} />
          <input
            type="text"
            placeholder="Buscá por nombre..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full h-12 pl-10 pr-4 border-2 border-gray-medium rounded-lg
                     focus:outline-none focus:border-blue-industrial transition-colors"
          />
        </div>
        <p className="text-sm text-gray-text mt-2">
          Ejemplos: "transmisión", "refrigeración", "batería"
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
