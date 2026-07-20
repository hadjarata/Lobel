import { CART_MAX_LINES, CART_MAX_QUANTITY, GUEST_CART_KEY } from './cartConstants';

const validLine = (line) => (
  line && Number.isInteger(line.variant_id) && line.variant_id > 0
  && Number.isInteger(line.quantity) && line.quantity > 0
  && line.quantity <= CART_MAX_QUANTITY
);

const createId = () => globalThis.crypto?.randomUUID?.()
  || `guest-${Date.now()}-${Math.random().toString(16).slice(2)}`;

export const sanitizeGuestCart = (value) => {
  const input = Array.isArray(value?.items) ? value.items : [];
  const byVariant = new Map();
  input.filter(validLine).slice(0, CART_MAX_LINES).forEach((line) => {
    const previous = byVariant.get(line.variant_id);
    byVariant.set(line.variant_id, {
      variant_id: line.variant_id,
      quantity: Math.min(CART_MAX_QUANTITY, (previous?.quantity || 0) + line.quantity),
      added_at: previous?.added_at || (
        typeof line.added_at === 'string' ? line.added_at : new Date().toISOString()
      ),
    });
  });
  return {
    id: typeof value?.id === 'string' && value.id ? value.id : createId(),
    revision: Number.isInteger(value?.revision) && value.revision >= 0 ? value.revision : 0,
    pending_merge_key: typeof value?.pending_merge_key === 'string'
      ? value.pending_merge_key : null,
    items: [...byVariant.values()],
  };
};

export const readGuestCart = (storage = localStorage) => {
  try {
    const raw = storage.getItem(GUEST_CART_KEY);
    const cart = sanitizeGuestCart(raw ? JSON.parse(raw) : {});
    storage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
    return cart;
  } catch {
    const cart = sanitizeGuestCart({});
    storage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
    return cart;
  }
};

export const writeGuestCart = (value, storage = localStorage) => {
  const cart = sanitizeGuestCart({ ...value, revision: (value.revision || 0) + 1 });
  storage.setItem(GUEST_CART_KEY, JSON.stringify(cart));
  return cart;
};

export const addGuestLine = (variantId, quantity, storage = localStorage) => {
  if (!Number.isInteger(quantity) || quantity < 1) throw new TypeError('invalid_quantity');
  const cart = readGuestCart(storage);
  const existing = cart.items.find((line) => line.variant_id === variantId);
  if (!existing && cart.items.length >= CART_MAX_LINES) throw new RangeError('cart_line_limit');
  if (existing) existing.quantity = Math.min(CART_MAX_QUANTITY, existing.quantity + quantity);
  else cart.items.push({ variant_id: variantId, quantity, added_at: new Date().toISOString() });
  cart.pending_merge_key = null;
  return writeGuestCart(cart, storage);
};

export const updateGuestLine = (variantId, quantity, storage = localStorage) => {
  if (!Number.isInteger(quantity) || quantity < 1 || quantity > CART_MAX_QUANTITY) {
    throw new TypeError('invalid_quantity');
  }
  const cart = readGuestCart(storage);
  const line = cart.items.find((item) => item.variant_id === variantId);
  if (line) line.quantity = quantity;
  cart.pending_merge_key = null;
  return writeGuestCart(cart, storage);
};

export const removeGuestLine = (variantId, storage = localStorage) => {
  const cart = readGuestCart(storage);
  cart.items = cart.items.filter((line) => line.variant_id !== variantId);
  cart.pending_merge_key = null;
  return writeGuestCart(cart, storage);
};

export const clearGuestCartStorage = (storage = localStorage) => writeGuestCart({
  id: createId(), revision: 0, pending_merge_key: null, items: [],
}, storage);

export const ensureMergeKey = (storage = localStorage) => {
  const cart = readGuestCart(storage);
  if (!cart.pending_merge_key) {
    cart.pending_merge_key = createId();
    return writeGuestCart(cart, storage);
  }
  return cart;
};

