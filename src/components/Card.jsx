import React from 'react';

const Card = ({ children, title, subtitle, className = '' }) => {
  return (
    <div className={`card ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="text-xl font-semibold text-blue-industrial">{title}</h3>
          {subtitle && <p className="text-sm text-gray-text mt-1">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
