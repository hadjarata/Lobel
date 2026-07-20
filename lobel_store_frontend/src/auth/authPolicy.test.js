import { describe, expect, it } from 'vitest';
import { canReplayAfterAuthFailure } from './authConstants';

const expired = { status: 401, data: { code: 'token_not_valid' } };
describe('politique de rejeu', () => {
  it.each(['get', 'GET', 'head', 'options'])('autorise %s', (method) => {
    expect(canReplayAfterAuthFailure({ method }, expired)).toBe(true);
  });
  it.each(['post', 'put', 'patch', 'delete'])('refuse %s', (method) => {
    expect(canReplayAfterAuthFailure({ method }, expired)).toBe(false);
  });
  it('refuse une création de paiement', () => {
    expect(canReplayAfterAuthFailure({ method: 'post', url: '/api/payments/checkout/' }, expired)).toBe(false);
  });
  it('refuse une création de commande', () => {
    expect(canReplayAfterAuthFailure({ method: 'post', url: '/api/orders/orders/' }, expired)).toBe(false);
  });
  it('refuse un 403 métier', () => expect(canReplayAfterAuthFailure({ method: 'get' }, { status: 403 })).toBe(false));
  it('refuse un 401 sans code JWT', () => {
    expect(canReplayAfterAuthFailure({ method: 'get' }, { status: 401, data: {} })).toBe(false);
  });
  it('refuse un second rejeu', () => {
    expect(canReplayAfterAuthFailure({ method: 'get', _authRetried: true }, expired)).toBe(false);
  });
  it('refuse le client public', () => {
    expect(canReplayAfterAuthFailure({ method: 'get', skipAuthRefresh: true }, expired)).toBe(false);
  });
});
