import api from "./axios";
import { ENDPOINTS } from './endpoints';

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
