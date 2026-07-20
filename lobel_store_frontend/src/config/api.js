import { publicConfig } from './env';

export const API_BASE_URL = publicConfig.apiBaseUrl;

export const getApiBaseUrl = () => API_BASE_URL;

export const getFrontendOrigin = () => {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  return API_BASE_URL;
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
    return url;
  }

  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
};
