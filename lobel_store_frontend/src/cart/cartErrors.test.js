import { describe, expect, it } from 'vitest';
import { normalizeCartError } from './cartErrors';

describe('cart error categories', () => {
  it.each([
    'invalid_variant', 'inactive_variant', 'inactive_product',
    'insufficient_stock', 'invalid_quantity', 'idempotency_conflict',
  ])('maps backend code %s', (code) => {
    const error = normalizeCartError({ response: { status: 400, data: { code } } });
    expect(error.code).toBe(code);
    expect(error.message).toBeTruthy();
  });
  it('preserves available quantity', () => {
    expect(normalizeCartError({ response: { data: {
      code: 'insufficient_stock', available_quantity: 3,
    } } }).availableQuantity).toBe(3);
  });
  it('normalizes network failures', () => {
    expect(normalizeCartError(new Error('network')).code).toBe('network_error');
  });
  it('normalizes canceled requests', () => {
    expect(normalizeCartError({ code: 'ERR_CANCELED' }).isCanceled).toBe(true);
  });
  it('does not turn an absent amount into zero', () => {
    expect(normalizeCartError({ response: { data: { code: 'cart_error' } } }).availableQuantity).toBeNull();
  });
});
