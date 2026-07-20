import { beforeEach, describe, expect, it } from 'vitest';
import {
  addGuestLine, clearGuestCartStorage, ensureMergeKey, readGuestCart,
  removeGuestLine, sanitizeGuestCart, updateGuestLine, writeGuestCart,
} from './cartStorage';
import { CART_MAX_LINES, CART_MAX_QUANTITY, GUEST_CART_KEY } from './cartConstants';

const memoryStorage = () => {
  const data = new Map();
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => data.set(key, String(value)),
    removeItem: (key) => data.delete(key),
  };
};

describe('versioned guest cart storage', () => {
  let storage;
  beforeEach(() => { storage = memoryStorage(); });

  it('creates an empty versioned cart', () => {
    expect(readGuestCart(storage)).toMatchObject({ items: [], revision: 0 });
  });
  it('persists under the single documented key', () => {
    readGuestCart(storage);
    expect(storage.getItem(GUEST_CART_KEY)).toContain('"items":[]');
  });
  it('restores a valid line', () => {
    storage.setItem(GUEST_CART_KEY, JSON.stringify({ items: [{ variant_id: 4, quantity: 2 }] }));
    expect(readGuestCart(storage).items[0]).toMatchObject({ variant_id: 4, quantity: 2 });
  });
  it.each([null, 4, 'bad', [], { items: 'bad' }])('sanitizes malformed root %o', (value) => {
    expect(sanitizeGuestCart(value).items).toEqual([]);
  });
  it.each([
    {}, { variant_id: 0, quantity: 1 }, { variant_id: -1, quantity: 1 },
    { variant_id: '1', quantity: 1 }, { variant_id: 1, quantity: 0 },
    { variant_id: 1, quantity: -1 }, { variant_id: 1, quantity: 1.5 },
    { variant_id: 1, quantity: '1' }, { variant_id: 1, quantity: 100 },
  ])('removes invalid line %o', (line) => {
    expect(sanitizeGuestCart({ items: [line] }).items).toEqual([]);
  });
  it('recovers corrupted JSON and replaces it', () => {
    storage.setItem(GUEST_CART_KEY, '{');
    expect(readGuestCart(storage).items).toEqual([]);
    expect(() => JSON.parse(storage.getItem(GUEST_CART_KEY))).not.toThrow();
  });
  it('adds a new variant', () => {
    expect(addGuestLine(7, 2, storage).items[0]).toMatchObject({ variant_id: 7, quantity: 2 });
  });
  it('deduplicates a variant during addition', () => {
    addGuestLine(7, 2, storage);
    expect(addGuestLine(7, 3, storage).items).toEqual([
      expect.objectContaining({ variant_id: 7, quantity: 5 }),
    ]);
  });
  it('deduplicates corrupted duplicate lines during restoration', () => {
    const cart = sanitizeGuestCart({ items: [
      { variant_id: 2, quantity: 3 }, { variant_id: 2, quantity: 4 },
    ] });
    expect(cart.items).toHaveLength(1);
    expect(cart.items[0].quantity).toBe(7);
  });
  it('caps a cumulative quantity', () => {
    addGuestLine(1, 90, storage);
    expect(addGuestLine(1, 20, storage).items[0].quantity).toBe(CART_MAX_QUANTITY);
  });
  it.each([0, -1, 1.2, Number.NaN])('rejects addition quantity %o', (quantity) => {
    expect(() => addGuestLine(1, quantity, storage)).toThrow();
  });
  it('updates quantity explicitly', () => {
    addGuestLine(1, 1, storage);
    expect(updateGuestLine(1, 8, storage).items[0].quantity).toBe(8);
  });
  it.each([0, -1, 1.5, 100])('rejects update quantity %o', (quantity) => {
    addGuestLine(1, 1, storage);
    expect(() => updateGuestLine(1, quantity, storage)).toThrow();
  });
  it('removes by variant only', () => {
    addGuestLine(1, 1, storage); addGuestLine(2, 1, storage);
    expect(removeGuestLine(1, storage).items.map((line) => line.variant_id)).toEqual([2]);
  });
  it('ignores removal of an absent variant', () => {
    expect(removeGuestLine(8, storage).items).toEqual([]);
  });
  it('clears all lines and rotates identity', () => {
    const before = addGuestLine(1, 1, storage);
    const after = clearGuestCartStorage(storage);
    expect(after.items).toEqual([]);
    expect(after.id).not.toBe(before.id);
  });
  it('increments the revision on writes', () => {
    const cart = readGuestCart(storage);
    expect(writeGuestCart(cart, storage).revision).toBe(1);
  });
  it('creates a stable pending merge key', () => {
    const first = ensureMergeKey(storage);
    const second = ensureMergeKey(storage);
    expect(second.pending_merge_key).toBe(first.pending_merge_key);
  });
  it('invalidates pending merge key after a mutation', () => {
    ensureMergeKey(storage);
    expect(addGuestLine(1, 1, storage).pending_merge_key).toBeNull();
  });
  it('contains no token or personal fields', () => {
    addGuestLine(1, 1, storage);
    expect(storage.getItem(GUEST_CART_KEY)).not.toMatch(/token|email|address|phone|price|stock/i);
  });
  it('applies the line limit while sanitizing', () => {
    const items = Array.from({ length: CART_MAX_LINES + 5 }, (_, index) => ({
      variant_id: index + 1, quantity: 1,
    }));
    expect(sanitizeGuestCart({ items }).items).toHaveLength(CART_MAX_LINES);
  });
  it('refuses a new line after the line limit', () => {
    writeGuestCart({ items: Array.from({ length: CART_MAX_LINES }, (_, index) => ({
      variant_id: index + 1, quantity: 1,
    })) }, storage);
    expect(() => addGuestLine(1000, 1, storage)).toThrow('cart_line_limit');
  });
  it('preserves the first added timestamp when merging duplicates', () => {
    const cart = sanitizeGuestCart({ items: [
      { variant_id: 1, quantity: 1, added_at: 'first' },
      { variant_id: 1, quantity: 1, added_at: 'second' },
    ] });
    expect(cart.items[0].added_at).toBe('first');
  });
});

