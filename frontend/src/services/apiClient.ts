/**
 * Axios instance for all BookRover API calls.
 *
 * All requests go through this instance. The base URL is configured via
 * the VITE_API_BASE_URL environment variable (falls back to /api for the
 * Vite dev server proxy, which proxies to the FastAPI backend on port 8000).
 */

import axios from 'axios';

const TOKEN_KEY = 'bookrover_token';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the stored Bearer token to every outgoing request.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;
