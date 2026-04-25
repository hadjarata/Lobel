import api from "./axios";
import { ENDPOINTS } from './endpoints';

const getOrderList = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
};

const syncCartCount = (cart, notify = true) => {
  const cartCount = cart?.cart_items ?? 0;
  localStorage.setItem('cartCount', String(cartCount));

  if (notify) {
    window.dispatchEvent(new Event('cartUpdated'));
  }
};

export const fetchCart = async ({ notify = true } = {}) => {
  const response = await api.get(ENDPOINTS.ORDERS);
  const orders = getOrderList(response.data);
  const cart =
    orders.find((order) => order.complete === false) ??
    orders[0] ??
    null;

  syncCartCount(cart, notify);
  console.log("Cart data:", cart);

  return cart;
};

// ajouter un produit au panier (order item)
export const addOrderItem = async (data) => {
  const response = await api.post(ENDPOINTS.ORDER_ITEMS, data);
  return response.data;
};

// récupérer les items
export const getOrderItems = async () => {
  const response = await api.get(ENDPOINTS.ORDER_ITEMS);
  return response.data;
};

// supprimer un item
export const deleteOrderItem = async (id) => {
  const response = await api.delete(ENDPOINTS.ORDER_ITEM_DETAIL(id));
  return response.data;
};

// mettre à jour la quantité d'un item
export const updateOrderItem = async (id, data) => {
  const response = await api.put(ENDPOINTS.ORDER_ITEM_DETAIL(id), data);
  return response.data;
};

// vider le panier
export const clearCart = async () => {
  const response = await api.delete(ENDPOINTS.ORDER_ITEMS);
  return response.data;
};
