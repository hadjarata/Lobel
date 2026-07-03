import api from './axios';
import { ENDPOINTS } from './endpoints';

export const getOrders = async () => {
  const response = await api.get(ENDPOINTS.ORDERS);
  return response.data;
};

export const getOrderById = async (id) => {
  const response = await api.get(ENDPOINTS.ORDER_DETAIL(id));
  return response.data;
};
