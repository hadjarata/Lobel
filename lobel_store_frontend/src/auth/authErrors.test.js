import { describe, expect, it } from 'vitest';
import { AUTH_ERROR_CODES, normalizeAuthError } from './authErrors';

describe('erreurs auth', () => {
  it('normalise une panne réseau', () => expect(normalizeAuthError(new Error()).code).toBe(AUTH_ERROR_CODES.NETWORK));
  it('normalise 429 et Retry-After', () => {
    const error = normalizeAuthError({ response: { status: 429, data: {}, headers: { 'retry-after': '30' } } });
    expect(error.code).toBe(AUTH_ERROR_CODES.THROTTLED);
    expect(error.retryAfter).toBe('30');
  });
  it('normalise 500 sans supprimer une session', () => {
    expect(normalizeAuthError({ response: { status: 503, data: {} } }).code).toBe(AUTH_ERROR_CODES.SERVER);
  });
  it('normalise token expiré', () => {
    expect(normalizeAuthError({ response: { status: 401, data: { code: 'token_not_valid' } } }).code)
      .toBe(AUTH_ERROR_CODES.SESSION_EXPIRED);
  });
  it('normalise les identifiants invalides sans reprendre le texte serveur', () => {
    const error = normalizeAuthError({ response: { status: 401, data: { detail: 'Compte indisponible.' } } });
    expect(error.code).toBe(AUTH_ERROR_CODES.INVALID_CREDENTIALS);
    expect(error.message).not.toContain('indisponible');
  });
  it('mappe les champs 400', () => {
    const error = normalizeAuthError({ response: { status: 400, data: { password: ['Trop court.'] } } });
    expect(error.fieldErrors.password).toBe('Trop court.');
  });
});
