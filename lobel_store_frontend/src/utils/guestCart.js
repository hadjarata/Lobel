const GUEST_CART_KEY = 'lobel_guest_cart';

const readStore = () => {
  try {
    const raw = localStorage.getItem(GUEST_CART_KEY);
    if (!raw) {
      return { items: [] };
    }

    const parsed = JSON.parse(raw);
    return {
      items: Array.isArray(parsed?.items) ? parsed.items : [],
    };
  } catch {
    return { items: [] };
  }
};

const writeStore = (items) => {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify({ items }));
};

export const getGuestCartItems = () => readStore().items;

export const clearGuestCart = () => {
  writeStore([]);
};

export const addGuestCartItem = ({ product_id, quantity = 1, product = null }) => {
  const items = getGuestCartItems();
  const existing = items.find((item) => item.product_id === product_id);

  if (existing) {
    existing.quantity += quantity;
    if (product) {
      existing.product = { ...existing.product, ...product };
    }
  } else {
    items.push({
      localId: `guest-${product_id}`,
      product_id,
      quantity,
      product: product || { id: product_id },
      addedAt: new Date().toISOString(),
    });
  }

  writeStore(items);
  return items;
};

export const updateGuestCartItemQuantity = (productId, quantity) => {
  const items = getGuestCartItems();
  const index = items.findIndex((item) => item.product_id === productId);

  if (index === -1) {
    return items;
  }

  if (quantity < 1) {
    items.splice(index, 1);
  } else {
    items[index].quantity = quantity;
  }

  writeStore(items);
  return items;
};

export const removeGuestCartItem = (productId) => {
  const items = getGuestCartItems().filter((item) => item.product_id !== productId);
  writeStore(items);
  return items;
};

export const buildGuestCartPayload = (items = getGuestCartItems()) => {
  const normalizedItems = items.map((item) => ({
    id: item.localId,
    product_id: item.product_id,
    quantity: item.quantity,
    product: item.product,
    date_added: item.addedAt,
  }));

  const cart_total = normalizedItems.reduce(
    (sum, item) => sum + Number(item.product?.price || 0) * item.quantity,
    0,
  );

  const cart_items = normalizedItems.reduce((sum, item) => sum + item.quantity, 0);

  return {
    id: null,
    items: normalizedItems,
    cart_total,
    cart_items,
    complete: false,
    status: 'pending',
    isGuest: true,
  };
};

export const getGuestProductIdFromItem = (item) =>
  item?.product_id ?? item?.product?.id ?? null;
