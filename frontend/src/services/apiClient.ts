/**
 * Axios instance for all BookRover API calls.
 *
 * All requests go through this instance. The base URL is configured via
 * the VITE_API_BASE_URL environment variable (falls back to /api for the
 * Vite dev server proxy, which proxies to the FastAPI backend on port 8000).
 *
 * Token strategy:
 *   mock mode    — reads from localStorage (set by authService.storeToken)
 *   cognito mode — calls fetchAuthSession() from aws-amplify to get a
 *                  fresh Cognito ID token on every request
 */

import axios from 'axios';
import { fetchAuthSession } from 'aws-amplify/auth';

const TOKEN_KEY = 'bookrover_token';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach the correct Bearer token to every outgoing request.
apiClient.interceptors.request.use(async (config) => {
  if (import.meta.env.VITE_AUTH_MODE === 'cognito') {
    try {
      const { tokens } = await fetchAuthSession();
      const token = tokens?.idToken?.toString();
      if (token) config.headers.Authorization = `Bearer ${token}`;
    } catch {
      // Not authenticated — request proceeds without a token.
    }
  } else {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiClient;


