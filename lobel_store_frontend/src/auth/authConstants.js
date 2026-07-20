export const AUTH_STORAGE_KEY = 'lobelstore.auth.v1';
export const AUTH_STATUS = Object.freeze({
  INITIALIZING: 'initializing',
  AUTHENTICATED: 'authenticated',
  ANONYMOUS: 'anonymous',
});
export const ACCESS_EXPIRY_SKEW_SECONDS = 45;
export const SAFE_REPLAY_METHODS = new Set(['get', 'head', 'options']);
export const canReplayAfterAuthFailure = (config, response) => (
  response?.status === 401
  && response?.data?.code === 'token_not_valid'
  && SAFE_REPLAY_METHODS.has(config?.method?.toLowerCase())
  && !config?._authRetried
  && !config?.skipAuthRefresh
);
