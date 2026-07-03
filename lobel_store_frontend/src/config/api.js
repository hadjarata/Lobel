/**
 * Configuration réseau API – développement sans IP fixe.
 *
 * En DEV (Vite) :
 *   - baseURL vide → requêtes relatives /api/* proxifiées vers Django (127.0.0.1:8000)
 *   - fonctionne sur PC, téléphone, tout réseau Wi-Fi sans changer de config
 *
 * En PROD :
 *   - VITE_API_BASE_URL ou hostname:8000
 */

const stripTrailingSlash = (url) => url.replace(/\/$/, '');

const LOCAL_BACKEND_PATTERNS = [
  /^https?:\/\/127\.0\.0\.1:8000/i,
  /^https?:\/\/localhost:8000/i,
];

export const getApiBaseUrl = () => {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;

  if (fromEnv) {
    return stripTrailingSlash(fromEnv);
  }

  if (import.meta.env.DEV) {
    return '';
  }

  if (typeof window !== 'undefined' && window.location?.hostname) {
    return `http://${window.location.hostname}:8000`;
  }

  return 'http://127.0.0.1:8000';
};

export const API_BASE_URL = getApiBaseUrl();

export const getFrontendOrigin = () => {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }

  return import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173';
};

export const resolveMediaUrl = (url) => {
  if (!url) {
    return null;
  }

  if (
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('data:') ||
    url.startsWith('blob:')
  ) {
    if (import.meta.env.DEV && typeof window !== 'undefined') {
      for (const pattern of LOCAL_BACKEND_PATTERNS) {
        if (pattern.test(url)) {
          return url.replace(pattern, window.location.origin);
        }
      }
    }

    if (!import.meta.env.DEV && typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return url
          .replace('http://127.0.0.1:8000', `http://${hostname}:8000`)
          .replace('http://localhost:8000', `http://${hostname}:8000`);
      }
    }

    return url;
  }

  const base = getApiBaseUrl();

  if (import.meta.env.DEV && !base) {
    return url.startsWith('/') ? url : `/${url}`;
  }

  return `${base}${url.startsWith('/') ? url : `/${url}`}`;
};
