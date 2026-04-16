import api from "../api/axios";
import { ENDPOINTS } from "../api/endpoints";

export const createPayment = async (paymentData) => {
  const response = await api.post(ENDPOINTS.PAYMENTS, paymentData);
  return response.data;
};

export const getPayments = async () => {
  const response = await api.get(ENDPOINTS.PAYMENTS);
  return response.data;
};