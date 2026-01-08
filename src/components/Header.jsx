import React, { useState } from 'react';
import { User, ShoppingCart, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useCliente, CLIENTES_DISPONIBLES } from '../context/ClienteContext';
import { useCart } from '../context/CartContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';

const Header = () => {
  const navigate = useNavigate();
  const { cuit, cambiarCliente } = useCliente();
  const { cantidadTotal } = useCart();
  const { data: perfil } = useApi(() => api.getPerfil(cuit), [cuit]);
  const [selectorAbierto, setSelectorAbierto] = useState(false);

  // Formatear CUIT: 30717287572 -> 30-71728757-2
  const formatCuit = (cuitNumber) => {
    if (!cuitNumber) return '';
    const cuitStr = cuitNumber.toString();
    if (cuitStr.length !== 11) return cuitStr;
    return `${cuitStr.slice(0, 2)}-${cuitStr.slice(2, 10)}-${cuitStr.slice(10)}`;
  };

  return (
    <header className="bg-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-mechanic to-orange-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">AP</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-blue-industrial">Portal B2B</h1>
              <p className="text-xs text-gray-text">Distribuidora Autopartes</p>
            </div>
          </div>

          {/* User Info and Cart */}
          <div className="flex items-center space-x-3">
            <div className="text-right hidden md:block">
              <p className="text-sm font-medium text-blue-industrial">
                {perfil?.nombre_empresa || 'Cargando...'}
              </p>
              <p className="text-xs text-gray-text">CUIT: {formatCuit(cuit)}</p>
            </div>

            {/* Carrito */}
            <button
              onClick={() => navigate('/carrito')}
              className="relative w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center hover:bg-orange-200 transition-colors"
            >
              <ShoppingCart className="w-5 h-5 text-orange-mechanic" />
              {cantidadTotal() > 0 && (
                <span className="absolute -top-1 -right-1 bg-orange-mechanic text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {cantidadTotal()}
                </span>
              )}
            </button>

            {/* Selector de Cliente */}
            <div className="relative">
              <button
                onClick={() => setSelectorAbierto(!selectorAbierto)}
                className="flex items-center gap-2 px-3 py-2 bg-blue-100 rounded-lg hover:bg-blue-200 transition-colors"
              >
                <User className="w-5 h-5 text-blue-industrial" />
                <ChevronDown className={`w-4 h-4 text-blue-industrial transition-transform ${selectorAbierto ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown de clientes */}
              {selectorAbierto && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setSelectorAbierto(false)}
                  />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border-2 border-blue-100 z-50">
                    <div className="p-2 border-b border-gray-200">
                      <p className="text-xs text-gray-500 font-semibold uppercase px-2">
                        Cambiar Cliente
                      </p>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      {CLIENTES_DISPONIBLES.map(cliente => (
                        <button
                          key={cliente.cuit}
                          onClick={() => {
                            cambiarCliente(cliente.cuit);
                            setSelectorAbierto(false);
                            // Recargar la página para refrescar todos los datos
                            window.location.reload();
                          }}
                          className={`w-full text-left px-4 py-3 hover:bg-blue-50 transition-colors ${
                            cuit === cliente.cuit ? 'bg-blue-100 border-l-4 border-blue-industrial' : ''
                          }`}
                        >
                          <p className="font-semibold text-blue-industrial text-sm">
                            {cliente.nombre}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            CUIT: {formatCuit(cliente.cuit)}
                          </p>
                          {cuit === cliente.cuit && (
                            <span className="text-xs text-blue-600 font-semibold mt-1 inline-block">
                              ✓ Seleccionado
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
