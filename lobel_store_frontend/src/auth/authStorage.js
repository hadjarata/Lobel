import { AUTH_STORAGE_KEY } from './authConstants';

const getBrowserStorage = () => (typeof window !== 'undefined' ? window.localStorage : null);
const isStoredSession = (value) => (
  value && typeof value === 'object' && typeof value.refresh === 'string' && value.refresh.length > 0
);

export const readStoredSession = () => {
  const storage = getBrowserStorage();
  if (!storage) return null;
  try {
    const parsed = JSON.parse(storage.getItem(AUTH_STORAGE_KEY));
    if (!isStoredSession(parsed)) {
      storage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }
    return { refresh: parsed.refresh };
  } catch {
    storage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

export const saveStoredSession = ({ refresh }) => {
  if (typeof refresh !== 'string' || !refresh) throw new TypeError('Un refresh token valide est requis.');
  getBrowserStorage()?.setItem(AUTH_STORAGE_KEY, JSON.stringify({ refresh }));
};
export const clearStoredSession = () => getBrowserStorage()?.removeItem(AUTH_STORAGE_KEY);
export const hasRestorableSession = () => Boolean(readStoredSession());
