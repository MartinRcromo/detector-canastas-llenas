// components/Loading.jsx
import React from 'react';

const Loading = ({ message = 'Cargando...' }) => {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-industrial mx-auto mb-4"></div>
        <p className="text-gray-text">{message}</p>
      </div>
    </div>
  );
};

export default Loading;
