import React from 'react';
import { Check, Plus } from 'lucide-react';
import * as Icons from 'lucide-react';

const FamiliaCard = ({ familia, isSelected, onClick }) => {
  const IconComponent = Icons[familia.icono] || Icons.Package;

  return (
    <div
      onClick={onClick}
      className={`
        relative cursor-pointer rounded-lg p-6 transition-all duration-200
        flex flex-col items-center justify-center gap-3 min-h-[140px]
        ${isSelected
          ? 'bg-blue-50 border-2 border-blue-industrial shadow-md'
          : 'bg-white border-2 border-gray-medium hover:border-blue-industrial hover:bg-gray-light'
        }
      `}
    >
      <IconComponent
        className={`${isSelected ? 'text-blue-industrial' : 'text-gray-text'}`}
        size={40}
      />
      <h3 className="text-sm font-medium text-gray-graphite text-center">
        {familia.nombre}
      </h3>
      <div className={`
        absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center
        ${isSelected ? 'bg-green-progress' : 'bg-gray-medium'}
      `}>
        {isSelected ? (
          <Check className="text-white" size={16} />
        ) : (
          <Plus className="text-gray-text" size={16} />
        )}
      </div>
    </div>
  );
};

export default FamiliaCard;
