import axios from 'axios';

// Dynamically resolve API URL: Custom localStorage override -> VITE_API_URL build env -> '/api'
export const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('gt_backend_url');
    if (custom && custom.trim()) {
      return custom.trim().replace(/\/+$/, '');
    }
  }
  return import.meta.env.VITE_API_URL || '/api';
};

const api = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl();
  const token = localStorage.getItem('gt_auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('gt_auth_token');
      localStorage.removeItem('gt_user');
      // If unauthorized on protected route, redirect to login
      if (
        typeof window !== 'undefined' &&
        window.location.pathname !== '/login' &&
        window.location.pathname !== '/register' &&
        window.location.pathname !== '/'
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
