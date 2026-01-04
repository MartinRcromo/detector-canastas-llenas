import React from 'react';
import { NavLink } from 'react-router-dom';
import { User, ShoppingCart, TrendingUp, Award } from 'lucide-react';

const Sidebar = () => {
  const menuItems = [
    { path: '/perfil', label: 'Mi Perfil', icon: User },
    { path: '/portfolio', label: 'Portfolio', icon: ShoppingCart },
    { path: '/oportunidades', label: 'Oportunidades', icon: TrendingUp },
    { path: '/planes', label: 'Planes', icon: Award },
  ];

  return (
    <aside className="w-64 bg-white shadow-md h-screen sticky top-16 hidden lg:block">
      <nav className="p-4">
        <div className="space-y-2">
          {menuItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-orange-mechanic text-white'
                    : 'text-gray-text hover:bg-gray-light hover:text-blue-industrial'
                }`
              }
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
