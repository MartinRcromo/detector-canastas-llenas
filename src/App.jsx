import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ProfilePage from './pages/ProfilePage';
import PortfolioPage from './pages/PortfolioPage';
import OpportunitiesPage from './pages/OpportunitiesPage';
import PlansPage from './pages/PlansPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/perfil" replace />} />
          <Route path="/perfil" element={<ProfilePage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/oportunidades" element={<OpportunitiesPage />} />
          <Route path="/planes" element={<PlansPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
