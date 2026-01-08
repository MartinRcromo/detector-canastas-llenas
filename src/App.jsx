import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ClienteProvider } from './context/ClienteContext';
import { CartProvider } from './context/CartContext';
import Layout from './components/Layout';
import ProfilePage from './pages/ProfilePage';
import PortfolioPage from './pages/PortfolioPage';
import OpportunitiesPage from './pages/OpportunitiesPage';
import PlansPage from './pages/PlansPage';
import CartPage from './pages/CartPage';

function App() {
  return (
    <ClienteProvider>
      <CartProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/perfil" replace />} />
              <Route path="/perfil" element={<ProfilePage />} />
              <Route path="/portfolio" element={<PortfolioPage />} />
              <Route path="/oportunidades" element={<OpportunitiesPage />} />
              <Route path="/planes" element={<PlansPage />} />
              <Route path="/carrito" element={<CartPage />} />
            </Routes>
          </Layout>
        </Router>
      </CartProvider>
    </ClienteProvider>
  );
}

export default App;
