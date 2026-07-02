import api from './axios';
import { ENDPOINTS } from './endpoints';

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
  const response = await api.get(ENDPOINTS.CART);
  const cart = normalizeCart(response.data);
  syncCartCount(cart, notify);
  return cart;
};

export const addOrderItem = async (data) => {
  const response = await api.post(ENDPOINTS.ORDER_ITEMS, data);
  await fetchCart({ notify: true });
  return response.data;
};

export const getOrderItems = async () => {
  const response = await api.get(ENDPOINTS.ORDER_ITEMS);
  return response.data;
};

export const deleteOrderItem = async (id) => {
  const response = await api.delete(ENDPOINTS.ORDER_ITEM_DETAIL(id));
  await fetchCart({ notify: true });
  return response.data;
};

export const updateOrderItem = async (id, data) => {
  const response = await api.put(ENDPOINTS.ORDER_ITEM_DETAIL(id), data);
  await fetchCart({ notify: true });
  return response.data;
};

export const clearCart = async () => {
  const response = await api.delete(ENDPOINTS.ORDER_ITEMS);
  await fetchCart({ notify: true });
  return response.data;
};
