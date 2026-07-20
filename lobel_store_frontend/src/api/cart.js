import api from './axios';
import publicApi from './publicAxios';
import { ENDPOINTS } from './endpoints';
import { adaptCart, adaptOrderItem } from './contracts/orders';
import { adaptResolvedVariant } from '../cart/variantModel';

export const fetchServerCart = (config = {}) => api.get(ENDPOINTS.CART, config)
  .then(({ data }) => adaptCart(data));

export const addServerCartItem = (variantId, quantity, config = {}) => api.post(
  ENDPOINTS.ORDER_ITEMS,
  { variant_id: variantId, quantity },
  config,
).then(({ data }) => adaptOrderItem(data));

export const updateServerCartItem = (itemId, quantity, config = {}) => api.patch(
  ENDPOINTS.ORDER_ITEM_DETAIL(itemId),
  { quantity },
  config,
).then(({ data }) => adaptOrderItem(data));

export const removeServerCartItem = (itemId, config = {}) => api.delete(
  ENDPOINTS.ORDER_ITEM_DETAIL(itemId),
  config,
);

export const clearServerCart = (config = {}) => api.delete(ENDPOINTS.CART_CLEAR, config)
  .then(({ data }) => adaptCart(data));

export const mergeGuestCart = (items, idempotencyKey, config = {}) => api.post(
  ENDPOINTS.CART_MERGE,
  { items: items.map(({ variant_id, quantity }) => ({ variant_id, quantity })) },
  {
    ...config,
    headers: { ...config.headers, 'Idempotency-Key': idempotencyKey },
  },
).then(({ data }) => ({
  ...data,
  cart: adaptCart(data.cart),
}));

export const resolveVariants = (variantIds, config = {}) => publicApi.post(
  ENDPOINTS.RESOLVE_VARIANTS,
  { variant_ids: variantIds },
  config,
).then(({ data }) => ({
  variants: data.results.map(adaptResolvedVariant),
  missingIds: data.missing_ids.map(Number),
}));

// Compatibility hook: CartProvider owns the authenticated merge lifecycle.
export const syncGuestCartToServer = async () => null;
export const fetchCart = fetchServerCart;
