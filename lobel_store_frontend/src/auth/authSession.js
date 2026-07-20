import { requestRefresh } from './authApi';
import { clearStoredSession, readStoredSession, saveStoredSession } from './authStorage';
import { isJwtExpired } from './jwt';
import { normalizeAuthError } from './authErrors';

let accessToken = null;
let refreshPromise = null;
let generation = 0;
const listeners = new Set();

const notify = (reason) => listeners.forEach((listener) => listener(reason));
export const getAccessToken = () => accessToken;
export const getRefreshToken = () => readStoredSession()?.refresh || null;
export const hasSession = () => Boolean(accessToken || getRefreshToken());
export const isAccessTokenUsable = () => Boolean(accessToken && !isJwtExpired(accessToken));
export const subscribeToSession = (listener) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};
export const establishSession = ({ access, refresh }) => {
  if (!access || !refresh) throw new TypeError('Réponse de session JWT incomplète.');
  generation += 1;
  accessToken = access;
  saveStoredSession({ refresh });
  notify('established');
};
export const clearSession = (reason = 'cleared') => {
  generation += 1;
  accessToken = null;
  refreshPromise = null;
  clearStoredSession();
  notify(reason);
};
export const refreshSession = async () => {
  if (refreshPromise) return refreshPromise;
  const refresh = getRefreshToken();
  if (!refresh) throw normalizeAuthError({ response: { status: 401, data: {} } });
  const startedGeneration = generation;
  refreshPromise = requestRefresh(refresh)
    .then((tokens) => {
      if (generation !== startedGeneration) {
        throw new DOMException('Session remplacée pendant le renouvellement.', 'AbortError');
      }
      if (!tokens?.access) throw new TypeError('Réponse de refresh JWT incomplète.');
      accessToken = tokens.access;
      saveStoredSession({ refresh: tokens.refresh || refresh });
      notify('refreshed');
      return accessToken;
    })
    .catch((error) => {
      if (error?.name === 'AbortError') throw error;
      const normalized = normalizeAuthError(error);
      if ([400, 401, 403].includes(normalized.status)) clearSession('expired');
      throw normalized;
    })
    .finally(() => {
      if (generation === startedGeneration) refreshPromise = null;
    });
  return refreshPromise;
};
export const getValidAccessToken = () => (
  isAccessTokenUsable() ? Promise.resolve(accessToken) : refreshSession()
);
export const __resetAuthSessionForTests = () => {
  accessToken = null;
  refreshPromise = null;
  generation = 0;
  listeners.clear();
};
