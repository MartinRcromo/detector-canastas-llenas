import React from 'react';
import { formatCurrency, formatNumber } from '../utils/formatters';

const MetricCard = ({ label, value, type = 'number', icon: Icon }) => {
  const formatValue = () => {
    if (type === 'currency') return formatCurrency(value);
    if (type === 'number') return formatNumber(value);
    return value;
  };

  return (
    <div className="metric-card">
      {Icon && (
        <div className="flex justify-center mb-3">
          <div className="p-2 bg-orange-50 rounded-lg">
            <Icon className="w-6 h-6 text-orange-mechanic" />
          </div>
        </div>
      )}
      <div className="metric-value">{formatValue()}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
};

export default MetricCard;
