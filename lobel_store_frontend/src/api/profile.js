import api from './axios';
import { ENDPOINTS } from './endpoints';
import { adaptCustomer } from './contracts/customer';
import { normalizeApiError } from '../utils/apiErrors';

export const getCustomerProfile = () => api.get(ENDPOINTS.CURRENT_USER)
  .then(({ data }) => adaptCustomer(data));

export const updateCustomerProfile = async (customerId, payload) => {
  try {
    const { data } = await api.patch(ENDPOINTS.CUSTOMER_DETAIL(customerId), payload);
    return adaptCustomer(data);
  } catch (error) {
    throw normalizeApiError(error, 'Impossible de mettre à jour le profil.');
  }
};
