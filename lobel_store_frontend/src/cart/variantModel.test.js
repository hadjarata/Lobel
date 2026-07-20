import { describe, expect, it } from 'vitest';
import {
  adaptResolvedVariant, availableVariants, compatibleValues,
  findSelectedVariant, initialVariantSelection,
} from './variantModel';

const variant = (id, color, size, stock = 2, extra = {}) => ({
  id, product_id: 1, product_name: 'Robe', sku: `SKU-${id}`,
  color: color ? { id: color, name: `C${color}` } : null,
  size: size ? { id: size, name: `S${size}` } : null,
  attributes: {}, price: '10.50', stock, is_available: stock > 0,
  is_active: true, image: null, ...extra,
});

describe('variant model and selection', () => {
  it('normalizes the complete backend model', () => {
    expect(adaptResolvedVariant(variant(1, 1, 1))).toMatchObject({
      id: 1, product_id: 1, price: '10.50', stock: 2, is_available: true,
    });
  });
  it('preserves decimal price as a string', () => {
    expect(adaptResolvedVariant({ ...variant(1, 1, 1), price: '0.10' }).price).toBe('0.10');
  });
  it('does not invent an absent price', () => {
    expect(adaptResolvedVariant({ ...variant(1, 1, 1), price: null }).price).toBeNull();
  });
  it.each([null, {}, { id: 'bad', stock: 1 }])('rejects invalid variant %o', (value) => {
    expect(() => adaptResolvedVariant(value)).toThrow();
  });
  it.each([null, '2', 1.5, Number.NaN])('rejects invalid stock %o', (stock) => {
    expect(() => adaptResolvedVariant({ ...variant(1, 1, 1), stock })).toThrow();
  });
  it('filters out zero stock', () => {
    expect(availableVariants([variant(1, 1, 1, 0)])).toEqual([]);
  });
  it('filters out explicit unavailability', () => {
    expect(availableVariants([variant(1, 1, 1, 2, { is_available: false })])).toEqual([]);
  });
  it('filters out inactive variants', () => {
    expect(availableVariants([variant(1, 1, 1, 2, { is_active: false })])).toEqual([]);
  });
  it('auto-selects one unambiguous variant', () => {
    expect(initialVariantSelection([variant(7, 1, 1)])).toBe(7);
  });
  it('does not select an unavailable unique variant', () => {
    expect(initialVariantSelection([variant(7, 1, 1, 0)])).toBeNull();
  });
  it('does not arbitrarily select between variants', () => {
    expect(initialVariantSelection([variant(1, 1, 1), variant(2, 2, 1)])).toBeNull();
  });
  it('returns compatible colors for a selected size', () => {
    const values = compatibleValues(
      [variant(1, 1, 1), variant(2, 2, 2), variant(3, 3, 1)],
      { size: 1 }, 'color',
    );
    expect(values.map(({ id }) => id)).toEqual([1, 3]);
  });
  it('returns compatible sizes for a selected color', () => {
    const values = compatibleValues(
      [variant(1, 1, 1), variant(2, 1, 2), variant(3, 2, 3)],
      { color: 1 }, 'size',
    );
    expect(values.map(({ id }) => id)).toEqual([1, 2]);
  });
  it('excludes unavailable combinations', () => {
    const values = compatibleValues(
      [variant(1, 1, 1), variant(2, 1, 2, 0)], { color: 1 }, 'size',
    );
    expect(values.map(({ id }) => id)).toEqual([1]);
  });
  it('deduplicates attribute values', () => {
    expect(compatibleValues(
      [variant(1, 1, 1), variant(2, 1, 2)], {}, 'color',
    )).toHaveLength(1);
  });
  it('finds an exact color and size combination', () => {
    expect(findSelectedVariant(
      [variant(1, 1, 1), variant(2, 1, 2)], { color: 1, size: 2 },
    ).id).toBe(2);
  });
  it('does not construct a missing combination', () => {
    expect(findSelectedVariant(
      [variant(1, 1, 1), variant(2, 2, 2)], { color: 1, size: 2 },
    )).toBeNull();
  });
  it('supports a product without color', () => {
    expect(findSelectedVariant([variant(1, null, 1)], { size: 1 }).id).toBe(1);
  });
  it('supports a product without size', () => {
    expect(findSelectedVariant([variant(1, 1, null)], { color: 1 }).id).toBe(1);
  });
  it('keeps generic attributes from the backend', () => {
    const adapted = adaptResolvedVariant({ ...variant(1, 1, 1), attributes: { material: 'coton' } });
    expect(adapted.attributes).toEqual({ material: 'coton' });
  });
});

