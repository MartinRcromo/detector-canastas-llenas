import React from 'react';
import { formatPercentage } from '../utils/formatters';

const ProgressBar = ({ current, target, label, showPercentage = true }) => {
  const percentage = Math.min((current / target) * 100, 100);

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-text">{label}</span>
          {showPercentage && (
            <span className="text-sm font-semibold text-blue-industrial">
              {formatPercentage(percentage)}
            </span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-medium rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-orange-mechanic to-orange-600 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
