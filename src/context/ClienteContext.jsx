// context/ClienteContext.jsx
import React, { createContext, useContext, useState } from 'react';

const ClienteContext = createContext();

// CUIT por defecto para desarrollo - Chapa Rolo S.R.L. - ahora Frimar
const DEFAULT_CUIT =  '20211152800'; 

// Lista de clientes disponibles para testing
export const CLIENTES_DISPONIBLES = [
  { cuit: '30717287572', nombre: 'Chapa Rolo S.R.L.' },
  { cuit: '30123456789', nombre: 'Frimar' },
  { cuit: '30987654321', nombre: 'Cliente Demo 1' },
  { cuit: '30111222333', nombre: 'Cliente Demo 2' },
];

export function ClienteProvider({ children }) {
  const [cuit, setCuit] = useState(DEFAULT_CUIT);

  const cambiarCliente = (nuevoCuit) => {
    setCuit(nuevoCuit);
    // Limpiar carrito al cambiar cliente
    localStorage.removeItem('carrito');
  };

  return (
    <ClienteContext.Provider value={{ cuit, setCuit, cambiarCliente }}>
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
