import api from './axios';
import { ENDPOINTS } from './endpoints';
import { normalizeApiError } from '../utils/apiErrors';
import { adaptPagination } from './pagination';
import {
  adaptCheckoutSession,
  adaptPaymentDetail,
  adaptPaymentListItem,
} from './contracts/payments';

export const initializePayment = async ({ orderId, idempotencyKey }) => {
  try {
    const { data } = await api.post(
      ENDPOINTS.CHECKOUT,
      { order_id: orderId },
      {
        skipAuthRefresh: true,
        headers: { 'Idempotency-Key': idempotencyKey },
      },
    );
    return adaptCheckoutSession(data);
  } catch (error) {
    throw normalizeApiError(error, 'Impossible de démarrer le paiement.');
  }
};
export const refreshPaymentStatus = (paymentId) => api.post(
  ENDPOINTS.PAYMENT_REFRESH(paymentId), {}, { skipAuthRefresh: true },
).then(({ data }) => adaptPaymentDetail(data));
export const recordPaymentRedirect = (paymentId) => api.post(
  ENDPOINTS.PAYMENT_REDIRECTED(paymentId), {}, { skipAuthRefresh: true },
).then(({ data }) => data);
export const confirmMockPayment = (paymentId) => api.post(
  ENDPOINTS.MOCK_CONFIRM,
  { paymentId },
).then(({ data }) => data);
export const getPayments = (filters = {}) => api.get(ENDPOINTS.PAYMENTS, { params: filters })
  .then(({ data }) => adaptPagination(data, adaptPaymentListItem));
export const getPaymentById = (id) => api.get(ENDPOINTS.PAYMENT_DETAIL(id))
  .then(({ data }) => adaptPaymentDetail(data));
