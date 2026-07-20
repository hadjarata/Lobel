import { describe, expect, it } from 'vitest';
import { ACCESS_EXPIRY_SKEW_SECONDS } from './authConstants';
import { isJwtExpired, readJwtExpiration } from './jwt';

const jwt = (payload) => {
  const body = btoa(JSON.stringify(payload)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  return `header.${body}.signature`;
};

describe('JWT expiration', () => {
  it('lit exp', () => expect(readJwtExpiration(jwt({ exp: 200 }))).toBe(200));
  it('accepte un access valide', () => expect(isJwtExpired(jwt({ exp: 200 }), 100)).toBe(false));
  it('refuse un access expiré', () => expect(isJwtExpired(jwt({ exp: 99 }), 100)).toBe(true));
  it('anticipe de 45 secondes', () => {
    expect(ACCESS_EXPIRY_SKEW_SECONDS).toBe(45);
    expect(isJwtExpired(jwt({ exp: 140 }), 100)).toBe(true);
  });
  it('accepte un token hors marge', () => expect(isJwtExpired(jwt({ exp: 146 }), 100)).toBe(false));
  it.each([null, '', 'abc', 'a.b', 'a.%%%.c', jwt({ sub: 1 })])(
    'considère un token malformé ou sans exp comme expiré',
    (token) => expect(isJwtExpired(token, 100)).toBe(true),
  );
});
