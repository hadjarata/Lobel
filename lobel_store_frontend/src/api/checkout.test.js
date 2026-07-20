import { beforeEach, describe, expect, it, vi } from 'vitest';

const api = {
  get: vi.fn(),
  post: vi.fn(),
};

vi.mock('./axios', () => ({ default: api }));

const {
  createCheckoutOrder,
  getDeliveryOptions,
  getPendingCheckoutOrder,
  previewCheckout,
} = await import('./checkout');

describe('API checkout', () => {
  beforeEach(() => vi.clearAllMocks());

  it('demande les livraisons avec une requête POST non rejouable', async () => {
    api.post.mockResolvedValue({ data: { delivery_methods: [] } });
    const address = { city: 'Bamako' };
    await getDeliveryOptions(address);
    expect(api.post).toHaveBeenCalledWith(
      '/api/orders/orders/checkout/delivery-options/',
      { shipping_address: address },
      { skipAuthRefresh: true },
    );
  });

  it('obtient un preview sans autoriser le rejeu automatique JWT', async () => {
    api.post.mockResolvedValue({ data: { checkout_version: 'a'.repeat(64) } });
    const payload = { delivery_method: 'standard' };
    await expect(previewCheckout(payload)).resolves.toMatchObject({
      checkout_version: 'a'.repeat(64),
    });
    expect(api.post).toHaveBeenCalledWith(
      '/api/orders/orders/checkout/preview/', payload, { skipAuthRefresh: true },
    );
  });

  it('crée la commande avec Idempotency-Key et sans rejeu JWT', async () => {
    api.post.mockResolvedValue({ data: { order: { id: 42 } } });
    await createCheckoutOrder({ checkout_version: 'v' }, 'key-42');
    expect(api.post).toHaveBeenCalledWith(
      '/api/orders/orders/checkout/create-order/',
      { checkout_version: 'v' },
      {
        skipAuthRefresh: true,
        headers: { 'Idempotency-Key': 'key-42' },
      },
    );
  });

  it('reprend une commande pending via GET', async () => {
    api.get.mockResolvedValue({ data: { order: { id: 42 } } });
    await expect(getPendingCheckoutOrder()).resolves.toEqual({ order: { id: 42 } });
  });

  it('normalise les erreurs réseau', async () => {
    api.post.mockRejectedValue({ code: 'ECONNABORTED' });
    await expect(previewCheckout({})).rejects.toMatchObject({ code: 'timeout' });
  });
});
