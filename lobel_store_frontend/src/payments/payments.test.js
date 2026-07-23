import { describe, expect, it } from 'vitest';
import { adaptCheckoutSession } from '../api/contracts/payments';
import {
  canRedirectPayment, isPaymentFinal, paymentPollDelay, safePaymentReturnPath,
} from './paymentPolicy';

const session = (overrides = {}) => ({
  checkout_url: 'https://app.ligdicash.com/pay/session',
  payment_id: 1, order_id: 7, status: 'redirect_required',
  provider: 'ligdicash', amount: '5000.00', currency: 'XOF',
  ...overrides,
});

describe('sécurité des URLs de paiement', () => {
  const rejected = [
    'javascript:alert(1)', 'data:text/html,x', '//app.ligdicash.com/pay',
    'http://app.ligdicash.com/pay', 'https://evil.example/pay',
    'https://app.ligdicash.com.evil.example/pay',
    'https://user@app.ligdicash.com/pay', 'https://user:pass@app.ligdicash.com/pay',
    'ftp://app.ligdicash.com/pay', 'file:///tmp/pay',
    'blob:https://app.ligdicash.com/id', 'mailto:test@example.com',
    'tel:+22370000000', 'ws://app.ligdicash.com/pay',
    'wss://app.ligdicash.com/pay', 'not-an-url',
    'https:///pay', 'https://127.0.0.1/pay', 'https://localhost/pay',
    'https://[::1]/pay',
  ];
  it.each(rejected)('refuse %s', (url) => {
    expect(() => adaptCheckoutSession(session({ checkout_url: url }))).toThrow();
  });
});

describe('statuts de paiement', () => {
  it.each([
    ['completed', true], ['failed', true], ['cancelled', true], ['expired', true],
    ['refund_required', true],
    ['pending', false], ['processing', false], ['redirect_required', false],
    ['initializing', false], ['unknown', false], ['created', false],
  ])('%s final=%s', (status, expected) => {
    expect(isPaymentFinal(status)).toBe(expected);
  });
});

describe('polling borné', () => {
  it.each([
    [0, 2000], [1, 4000], [2, 8000], [3, 15000], [4, 15000],
    [5, 15000], [6, 15000], [7, 15000], [8, 15000], [-1, 2000],
  ])('tentative %s', (attempt, expected) => {
    expect(paymentPollDelay(attempt)).toBe(expected);
  });
});

describe('cohérence avant redirection', () => {
  it.each([
    [{}, true],
    [{ order_id: 8 }, false],
    [{ provider: 'evil' }, false],
    [{ status: 'pending' }, false],
    [{ checkout_url: '' }, false],
    [{ provider: 'mock' }, true],
    [{ status: 'completed' }, false],
    [{ order_id: null }, false],
    [{ checkout_url: null }, false],
    [{ provider: '' }, false],
  ])('variante %#', (overrides, expected) => {
    expect(canRedirectPayment(session(overrides), 7)).toBe(expected);
  });
});

describe('retour navigateur non autoritatif', () => {
  it.each([
    '', '?success=true', '?status=completed', '?amount=1',
    '?payment_id=999', '?order_id=999', '?provider=evil',
    '?token=secret', '?success=true&amount=0', '#completed',
  ])('ignore les paramètres %s', () => {
    expect(safePaymentReturnPath()).toBe('/checkout/payment/return');
  });
});

describe('contrat PaymentSession', () => {
  it.each([
    ['payment_id', null], ['order_id', null], ['status', null],
    ['provider', null], ['amount', null], ['currency', null],
  ])('refuse le champ absent %s', (field) => {
    const value = session();
    delete value[field];
    expect(() => adaptCheckoutSession(value)).toThrow();
  });
});

describe('sessions acceptées', () => {
  it('accepte LigdiCash HTTPS', () => {
    expect(adaptCheckoutSession(session()).provider).toBe('ligdicash');
  });
  it('ne transforme pas checkout_url en preuve de succès', () => {
    expect(adaptCheckoutSession(session()).status).toBe('redirect_required');
  });
  it('conserve le montant comme chaîne', () => {
    expect(adaptCheckoutSession(session()).amount).toBe('5000.00');
  });
  it('n’expose aucun token fournisseur', () => {
    expect(adaptCheckoutSession(session())).not.toHaveProperty('session_token');
  });
});
