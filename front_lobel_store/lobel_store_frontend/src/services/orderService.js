import api from "../api/axios";
import { ENDPOINTS } from "../api/endpoints";

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