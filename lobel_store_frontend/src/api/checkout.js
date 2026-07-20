import api from './axios';
import { ENDPOINTS } from './endpoints';
import { normalizeApiError } from '../utils/apiErrors';

const request = async (operation, fallback) => {
  try {
    const { data } = await operation();
    return data;
  } catch (error) {
    throw normalizeApiError(error, fallback);
  }
};

export const getDeliveryOptions = (shippingAddress) => request(
  () => api.post(
    ENDPOINTS.CHECKOUT_DELIVERY_OPTIONS,
    { shipping_address: shippingAddress },
    { skipAuthRefresh: true },
  ),
  'Impossible de charger les modes de livraison.',
);

export const previewCheckout = (payload) => request(
  () => api.post(ENDPOINTS.CHECKOUT_PREVIEW, payload, { skipAuthRefresh: true }),
  'Impossible de recalculer la commande.',
);

export const createCheckoutOrder = (payload, idempotencyKey) => request(
  () => api.post(ENDPOINTS.CHECKOUT_CREATE_ORDER, payload, {
    skipAuthRefresh: true,
    headers: { 'Idempotency-Key': idempotencyKey },
  }),
  'Impossible de créer la commande.',
);

export const getPendingCheckoutOrder = () => request(
  () => api.get(ENDPOINTS.CHECKOUT_PENDING),
  'Impossible de rechercher une commande en attente.',
);
