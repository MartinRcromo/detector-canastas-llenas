// context/ClienteContext.jsx
import React, { createContext, useContext, useState } from 'react';

const ClienteContext = createContext();

// CUIT por defecto para desarrollo
const DEFAULT_CUIT = '20301234567';

export function ClienteProvider({ children }) {
  const [cuit, setCuit] = useState(DEFAULT_CUIT);

  return (
    <ClienteContext.Provider value={{ cuit, setCuit }}>
      {children}
    </ClienteContext.Provider>
  );
}

export function useCliente() {
  const context = useContext(ClienteContext);
  if (!context) {
    throw new Error('useCliente must be used within ClienteProvider');
  }
  return context;
}
