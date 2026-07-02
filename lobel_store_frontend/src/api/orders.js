import api from "./axios";
import { ENDPOINTS } from './endpoints';

// créer une commande
export const createOrder = async (orderData) => {
  const response = await api.post(ENDPOINTS.ORDERS, orderData);
  return response.data;
};

// récupérer les commandes
export const getOrders = async () => {
  const response = await api.get(ENDPOINTS.ORDERS);
  return response.data;
};

// détail commande
export const getOrderById = async (id) => {
  const response = await api.get(ENDPOINTS.ORDER_DETAIL(id));
  return response.data;
};

// mettre à jour une commande
export const updateOrder = async (id, orderData) => {
  const response = await api.put(ENDPOINTS.ORDER_DETAIL(id), orderData);
  return response.data;
};

// annuler une commande
export const cancelOrder = async (id) => {
  const response = await api.put(`${ENDPOINTS.ORDER_DETAIL(id)}/cancel/`);
  return response.data;
};
