import { ACCESS_EXPIRY_SKEW_SECONDS } from './authConstants';

export const readJwtExpiration = (token) => {
  if (typeof token !== 'string') return null;
  const parts = token.split('.');
  if (parts.length !== 3 || !parts[1]) return null;
  try {
    const normalized = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    const payload = JSON.parse(globalThis.atob(padded));
    return Number.isFinite(payload.exp) ? payload.exp : null;
  } catch {
    return null;
  }
};

export const isJwtExpired = (
  token,
  nowSeconds = Date.now() / 1000,
  skewSeconds = ACCESS_EXPIRY_SKEW_SECONDS,
) => {
  const expiration = readJwtExpiration(token);
  return expiration === null || expiration <= nowSeconds + skewSeconds;
};
