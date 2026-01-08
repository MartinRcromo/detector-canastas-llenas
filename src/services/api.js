// services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // PERFIL
  async getPerfil(cuit) {
    return this.request(`/api/perfil/${cuit}`);
  }

  // PORTFOLIO
  async getPortfolio(cuit) {
    return this.request(`/api/portfolio/${cuit}`);
  }

  // OPORTUNIDADES
  async getOportunidades(cuit) {
    return this.request(`/api/oportunidades/${cuit}`);
  }

  // ESTRATEGIAS (lazy loading)
  async getEstrategias(cuit, subrubro) {
    return this.request(`/api/oportunidades/${cuit}/estrategias/${encodeURIComponent(subrubro)}`);
  }

  // PLANES
  async getPlanes(cuit) {
    return this.request(`/api/planes/${cuit}`);
  }

  // HEALTH CHECK
  async healthCheck() {
    return this.request('/health');
  }
}

export const api = new ApiService();
export default api;
