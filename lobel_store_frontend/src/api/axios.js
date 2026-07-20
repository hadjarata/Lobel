import axios from 'axios';
import { API_BASE_URL } from '../config/api';
import {
  getAccessToken,
  getValidAccessToken,
  hasSession,
  refreshSession,
} from '../auth/authSession';
import { canReplayAfterAuthFailure } from '../auth/authConstants';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

api.interceptors.request.use(
  async (config) => {
    const token = config.skipAuthRefresh
      ? getAccessToken()
      : hasSession() ? await getValidAccessToken() : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    const canReplay = canReplayAfterAuthFailure(config, error.response);

    if (!canReplay) return Promise.reject(error);
    config._authRetried = true;
    const token = await refreshSession();
    config.headers.Authorization = `Bearer ${token}`;
    return api(config);
  },
);

export default api;
