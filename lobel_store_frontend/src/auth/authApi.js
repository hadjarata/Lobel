import publicApi from '../api/publicAxios';
import { ENDPOINTS } from '../api/endpoints';

export const requestLogin = (credentials, config = {}) => publicApi.post(ENDPOINTS.LOGIN, {
  username: credentials.email,
  password: credentials.password,
}, config).then(({ data }) => data);
export const requestRefresh = (refresh, config = {}) => (
  publicApi.post(ENDPOINTS.REFRESH_TOKEN, { refresh }, config).then(({ data }) => data)
);
export const requestLogout = (refresh, config = {}) => publicApi.post(ENDPOINTS.LOGOUT, { refresh }, config);
export const requestRegister = (payload, config = {}) => (
  publicApi.post(ENDPOINTS.REGISTER, payload, config).then(({ data }) => data)
);
export const requestPasswordReset = (payload, config = {}) => (
  publicApi.post(ENDPOINTS.PASSWORD_RESET_REQUEST, payload, config).then(({ data }) => data)
);
export const requestPasswordResetConfirmation = (payload, config = {}) => (
  publicApi.post(ENDPOINTS.PASSWORD_RESET_CONFIRM, payload, config).then(({ data }) => data)
);
export const requestEmailVerification = (payload, config = {}) => (
  publicApi.post(ENDPOINTS.VERIFY_EMAIL, payload, config).then(({ data }) => data)
);
