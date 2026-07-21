import { beforeEach, describe, expect, it, vi } from 'vitest';
import api from './axios';
import { ENDPOINTS } from './endpoints';
import { getBestSellers, getNewProducts } from './products';
import {
  pageFixture,
  productListFixture,
} from '../test/fixtures/apiContracts';

vi.mock('./axios', () => ({
  default: { get: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  api.get.mockResolvedValue({
    data: pageFixture([productListFixture]),
  });
});

describe('specialized Home product helpers', () => {
  it('returns the best-seller results directly as an array', async () => {
    const products = await getBestSellers();

    expect(Array.isArray(products)).toBe(true);
    expect(products).toHaveLength(1);
    expect(products[0].id).toBe(productListFixture.id);
    expect(api.get).toHaveBeenCalledWith(
      ENDPOINTS.BESTSELLERS,
      expect.objectContaining({ params: { page_size: 4 } }),
    );
  });

  it('returns the new-product results directly as an array', async () => {
    const products = await getNewProducts(6);

    expect(Array.isArray(products)).toBe(true);
    expect(products).toHaveLength(1);
    expect(products[0].name).toBe(productListFixture.name);
    expect(api.get).toHaveBeenCalledWith(
      ENDPOINTS.NEW_PRODUCTS,
      expect.objectContaining({ params: { page_size: 6 } }),
    );
  });
});
