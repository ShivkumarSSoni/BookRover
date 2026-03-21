/**
 * Axios instance for all BookRover API calls.
 *
 * All requests go through this instance. The base URL is configured via
 * the VITE_API_BASE_URL environment variable (falls back to /api for the
 * Vite dev server proxy, which proxies to the FastAPI backend on port 8000).
 */

import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
