import api from "./axios";
import { ENDPOINTS } from './endpoints';

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
