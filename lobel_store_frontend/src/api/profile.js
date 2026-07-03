import api from './axios';
import { ENDPOINTS } from './endpoints';
import { throwApiValidationError } from '../utils/apiErrors';

export const getCustomerProfile = async () => {
  const response = await api.get(ENDPOINTS.CURRENT_USER);
  return response.data;
};

export const updateCustomerProfile = async (customerId, payload) => {
  try {
    const response = await api.patch(ENDPOINTS.CUSTOMER_DETAIL(customerId), payload);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, 'Impossible de mettre à jour le profil.');
  }
};
