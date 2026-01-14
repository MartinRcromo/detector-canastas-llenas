import React from 'react';
import { Check } from 'lucide-react';

const FamiliaConfirmadaItem = ({ nombre, subfamilias }) => {
  return (
    <div className="flex items-center justify-between p-3 border-b border-gray-medium hover:bg-gray-light transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
          <Check className="text-green-progress" size={16} />
        </div>
        <div>
          <span className="font-medium text-gray-graphite">{nombre}</span>
          {subfamilias && (
            <span className="text-gray-text text-sm ml-1">{subfamilias}</span>
          )}
        </div>
      </div>
      <button className="text-gray-400 hover:text-blue-industrial text-sm font-medium transition-colors">
        Editar
      </button>
    </div>
  );
};

export default FamiliaConfirmadaItem;
