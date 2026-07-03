import api from './axios';
import { ENDPOINTS } from './endpoints';

export const getCustomerProfile = async () => {
  const response = await api.get(ENDPOINTS.CURRENT_USER);
  return response.data;
};

export const updateCustomerProfile = async (customerId, payload) => {
  const response = await api.patch(ENDPOINTS.CUSTOMER_DETAIL(customerId), payload);
  return response.data;
};
