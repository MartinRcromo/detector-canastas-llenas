// components/ErrorMessage.jsx
import React from 'react';
import Card from './Card';

const ErrorMessage = ({ title = 'Error', message, onRetry }) => {
  return (
    <Card className="bg-red-50 border-red-200">
      <div className="text-center py-8">
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-red-600 font-semibold mb-2">{title}</p>
        <p className="text-sm text-gray-text mb-4">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn-primary text-sm"
          >
            Reintentar
          </button>
        )}
      </div>
    </Card>
  );
};

export default ErrorMessage;
