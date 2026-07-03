import api from './axios';
import { ENDPOINTS } from './endpoints';
import { getFrontendOrigin } from '../config/api';
import { throwApiValidationError } from '../utils/apiErrors';

export const initiateCheckout = async () => {
  try {
    const response = await api.post(ENDPOINTS.CHECKOUT, {
      frontend_url: getFrontendOrigin(),
    });
    return response.data;
  } catch (error) {
    throwApiValidationError(error, 'Impossible de démarrer le paiement.');
  }
};

export const confirmMockPayment = async (paymentId) => {
  const response = await api.post(ENDPOINTS.MOCK_CONFIRM, { paymentId });
  return response.data;
};

export const createPayment = async (paymentData) => {
  const response = await api.post(ENDPOINTS.PAYMENTS, paymentData);
  return response.data;
};

export const getPayments = async () => {
  const response = await api.get(ENDPOINTS.PAYMENTS);
  return response.data;
};

export const getPaymentById = async (id) => {
  const response = await api.get(ENDPOINTS.PAYMENT_DETAIL(id));
  return response.data;
};

export const updatePayment = async (id, paymentData) => {
  const response = await api.put(ENDPOINTS.PAYMENT_DETAIL(id), paymentData);
  return response.data;
};
