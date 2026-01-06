import React from 'react';
import { User } from 'lucide-react';
import { useCliente } from '../context/ClienteContext';
import { useApi } from '../hooks/useApi';
import api from '../services/api';

const Header = () => {
  const { cuit } = useCliente();
  const { data: perfil } = useApi(() => api.getPerfil(cuit), [cuit]);

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

          {/* User Info */}
          <div className="flex items-center space-x-3">
            <div className="text-right hidden md:block">
              <p className="text-sm font-medium text-blue-industrial">
                {perfil?.nombre_empresa || 'Cargando...'}
              </p>
              <p className="text-xs text-gray-text">CUIT: {formatCuit(cuit)}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-blue-industrial" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
