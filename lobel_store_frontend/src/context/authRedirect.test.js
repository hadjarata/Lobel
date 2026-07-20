import { describe, expect, it } from 'vitest';
import { getSafeInternalRedirect } from '../auth/authRedirect';

describe('redirection après login', () => {
  it('restaure une route interne', () => expect(getSafeInternalRedirect({ pathname: '/profile', search: '?tab=orders' })).toBe('/profile?tab=orders'));
  it.each(['https://evil.example', '//evil.example', 'javascript:alert(1)', '/\\evil'])(
    'refuse %s',
    (target) => expect(getSafeInternalRedirect(target)).toBe('/'),
  );
  it('utilise le fallback sans destination', () => expect(getSafeInternalRedirect(null, '/shop')).toBe('/shop'));
});
