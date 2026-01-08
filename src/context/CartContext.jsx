import React, { createContext, useContext, useState, useEffect } from 'react';

const CartContext = createContext();

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart debe usarse dentro de CartProvider');
  }
  return context;
}

export function CartProvider({ children }) {
  const [items, setItems] = useState([]);

  // Cargar carrito desde localStorage al iniciar
  useEffect(() => {
    const carritoGuardado = localStorage.getItem('carrito');
    if (carritoGuardado) {
      try {
        setItems(JSON.parse(carritoGuardado));
      } catch (e) {
        console.error('Error cargando carrito:', e);
      }
    }
  }, []);

  // Guardar carrito en localStorage cada vez que cambie
  useEffect(() => {
    localStorage.setItem('carrito', JSON.stringify(items));
  }, [items]);

  // Agregar producto al carrito
  const agregarProducto = (producto, subrubro, estrategia) => {
    setItems(prev => {
      // Verificar si el producto ya existe
      const existe = prev.find(item => item.codigo === producto.codigo);

      if (existe) {
        // Si existe, incrementar cantidad
        return prev.map(item =>
          item.codigo === producto.codigo
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        );
      }

      // Si no existe, agregarlo
      return [
        ...prev,
        {
          codigo: producto.codigo,
          nombre: producto.nombre,
          precio: producto.precio,
          cantidad: 1,
          subrubro: subrubro,
          estrategia: estrategia, // 'probar' o 'fe'
          clasificacion_abc: producto.clasificacion_abc,
          demanda: producto.demanda,
          volumen_12m: producto.volumen_12m
        }
      ];
    });
  };

  // Agregar todos los productos de una estrategia
  const agregarEstrategia = (productos, subrubro, estrategia) => {
    productos.forEach(producto => {
      agregarProducto(producto, subrubro, estrategia);
    });
  };

  // Actualizar cantidad de un producto
  const actualizarCantidad = (codigo, nuevaCantidad) => {
    if (nuevaCantidad <= 0) {
      eliminarProducto(codigo);
      return;
    }

    setItems(prev =>
      prev.map(item =>
        item.codigo === codigo
          ? { ...item, cantidad: nuevaCantidad }
          : item
      )
    );
  };

  // Eliminar producto del carrito
  const eliminarProducto = (codigo) => {
    setItems(prev => prev.filter(item => item.codigo !== codigo));
  };

  // Vaciar carrito completo
  const vaciarCarrito = () => {
    setItems([]);
  };

  // Calcular total del carrito
  const calcularTotal = () => {
    return items.reduce((total, item) => total + (item.precio * item.cantidad), 0);
  };

  // Calcular cantidad total de items
  const cantidadTotal = () => {
    return items.reduce((total, item) => total + item.cantidad, 0);
  };

  // Agrupar items por subrubro
  const itemsPorSubrubro = () => {
    const agrupado = {};
    items.forEach(item => {
      if (!agrupado[item.subrubro]) {
        agrupado[item.subrubro] = [];
      }
      agrupado[item.subrubro].push(item);
    });
    return agrupado;
  };

  const value = {
    items,
    agregarProducto,
    agregarEstrategia,
    actualizarCantidad,
    eliminarProducto,
    vaciarCarrito,
    calcularTotal,
    cantidadTotal,
    itemsPorSubrubro
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
}
