import api from './axios';
import { ENDPOINTS } from './endpoints';
import {
  addGuestCartItem,
  buildGuestCartPayload,
  clearGuestCart,
  getGuestCartItems,
  getGuestProductIdFromItem,
  removeGuestCartItem,
  updateGuestCartItemQuantity,
} from '../utils/guestCart';

export const hasAuthToken = () => Boolean(localStorage.getItem('access'));

const normalizeCart = (data) => {
  if (!data || data.id == null) {
    return {
      id: null,
      items: [],
      cart_total: 0,
      cart_items: 0,
      complete: false,
      status: 'pending',
    };
  }

  return {
    ...data,
    items: Array.isArray(data.items) ? data.items : [],
  };
};

const syncCartCount = (cart, notify = true) => {
  const cartCount = cart?.cart_items ?? 0;
  localStorage.setItem('cartCount', String(cartCount));

  if (notify) {
    window.dispatchEvent(new Event('cartUpdated'));
  }
};

export const fetchCart = async ({ notify = true } = {}) => {
  if (!hasAuthToken()) {
    const cart = buildGuestCartPayload();
    syncCartCount(cart, notify);
    return cart;
  }

  const response = await api.get(ENDPOINTS.CART);
  const cart = normalizeCart(response.data);
  syncCartCount(cart, notify);
  return cart;
};

export const addToCart = async ({ product_id, quantity = 1, product = null }) => {
  if (!hasAuthToken()) {
    addGuestCartItem({ product_id, quantity, product });
    const cart = buildGuestCartPayload();
    syncCartCount(cart, true);
    return cart;
  }

  const response = await api.post(ENDPOINTS.ORDER_ITEMS, {
    product_id,
    quantity,
  });
  await fetchCart({ notify: true });
  return response.data;
};

/** @deprecated Préférer addToCart */
export const addOrderItem = async (data) => addToCart(data);

export const updateCartItemQuantity = async (item, quantity) => {
  if (!hasAuthToken()) {
    const productId = getGuestProductIdFromItem(item);
    updateGuestCartItemQuantity(productId, quantity);
    const cart = buildGuestCartPayload();
    syncCartCount(cart, true);
    return cart;
  }

  const response = await api.put(ENDPOINTS.ORDER_ITEM_DETAIL(item.id), { quantity });
  await fetchCart({ notify: true });
  return response.data;
};

export const removeCartItem = async (item) => {
  if (!hasAuthToken()) {
    const productId = getGuestProductIdFromItem(item);
    removeGuestCartItem(productId);
    const cart = buildGuestCartPayload();
    syncCartCount(cart, true);
    return cart;
  }

  const response = await api.delete(ENDPOINTS.ORDER_ITEM_DETAIL(item.id));
  await fetchCart({ notify: true });
  return response.data;
};

/** @deprecated Préférer updateCartItemQuantity */
export const updateOrderItem = async (id, data) =>
  updateCartItemQuantity({ id }, data.quantity);

/** @deprecated Préférer removeCartItem */
export const deleteOrderItem = async (id) => removeCartItem({ id });

export const syncGuestCartToServer = async () => {
  if (!hasAuthToken()) {
    return null;
  }

  const guestItems = getGuestCartItems();
  if (guestItems.length === 0) {
    return fetchCart({ notify: true });
  }

  let serverCart = await fetchCart({ notify: false });

  for (const guestItem of guestItems) {
    const existing = serverCart.items.find(
      (item) => item.product?.id === guestItem.product_id,
    );

    if (existing) {
      await api.put(ENDPOINTS.ORDER_ITEM_DETAIL(existing.id), {
        quantity: existing.quantity + guestItem.quantity,
      });
    } else {
      await api.post(ENDPOINTS.ORDER_ITEMS, {
        product_id: guestItem.product_id,
        quantity: guestItem.quantity,
      });
    }
  }

  clearGuestCart();
  serverCart = await fetchCart({ notify: true });
  return serverCart;
};

export const getOrderItems = async () => {
  const response = await api.get(ENDPOINTS.ORDER_ITEMS);
  return response.data;
};

export const clearCart = async () => {
  if (!hasAuthToken()) {
    clearGuestCart();
    const cart = buildGuestCartPayload();
    syncCartCount(cart, true);
    return cart;
  }

  const response = await api.delete(ENDPOINTS.ORDER_ITEMS);
  await fetchCart({ notify: true });
  return response.data;
};
