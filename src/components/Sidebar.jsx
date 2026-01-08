import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { User, ShoppingCart, TrendingUp, Award, Package, Menu, X } from 'lucide-react';
import { useCart } from '../context/CartContext';

const Sidebar = () => {
  const [menuAbierto, setMenuAbierto] = useState(false);
  const { cantidadTotal } = useCart();

  const menuItems = [
    { path: '/perfil', label: 'Mi Perfil', icon: User },
    { path: '/portfolio', label: 'Portfolio', icon: Package },
    { path: '/oportunidades', label: 'Oportunidades', icon: TrendingUp },
    { path: '/carrito', label: 'Mi Carrito', icon: ShoppingCart, badge: cantidadTotal() },
    { path: '/planes', label: 'Planes', icon: Award },
  ];

  return (
    <>
      {/* Botón móvil */}
      <button
        onClick={() => setMenuAbierto(!menuAbierto)}
        className="lg:hidden fixed bottom-4 right-4 z-50 w-14 h-14 bg-orange-mechanic text-white rounded-full shadow-lg flex items-center justify-center hover:bg-orange-600 transition-colors"
      >
        {menuAbierto ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Overlay móvil */}
      {menuAbierto && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setMenuAbierto(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        w-64 bg-white shadow-md h-screen sticky top-16
        lg:block
        ${menuAbierto ? 'fixed top-0 left-0 z-50 block' : 'hidden'}
      `}>
        <nav className="p-4 mt-16 lg:mt-0">
          <div className="space-y-2">
            {menuItems.map(({ path, label, icon: Icon, badge }) => (
              <NavLink
                key={path}
                to={path}
                onClick={() => setMenuAbierto(false)}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all relative ${
                    isActive
                      ? 'bg-orange-mechanic text-white'
                      : 'text-gray-text hover:bg-gray-light hover:text-blue-industrial'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{label}</span>
                {badge > 0 && (
                  <span className="ml-auto bg-orange-mechanic text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                    {badge}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;
