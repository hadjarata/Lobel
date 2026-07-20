import { ApiContractError, finiteInteger, nullableString, requireField, requireObject } from './contract';
import { adaptOrderDetail } from './orders';

const PAYMENT_STATUSES = new Set([
  'created', 'initializing', 'pending', 'redirect_required', 'processing',
  'completed', 'failed', 'cancelled', 'expired', 'unknown',
]);
const base = (raw, adapter) => {
  const data = requireObject(raw, adapter);
  const status = String(requireField(data, 'status', adapter));
  if (!PAYMENT_STATUSES.has(status)) throw new ApiContractError(adapter, 'status', status);
  return {
    ...data,
    id: finiteInteger(requireField(data, 'id', adapter), adapter, 'id'),
    amount: String(requireField(data, 'amount', adapter)),
    status,
    payment_method: String(requireField(data, 'payment_method', adapter)),
    provider: String(requireField(data, 'provider', adapter)),
    currency: nullableString(data.currency) || 'XOF',
    processed_at: nullableString(data.processed_at),
    date_paid: nullableString(data.date_paid),
  };
};
export const adaptPaymentListItem = (raw) => {
  const payment = base(raw, 'payment-list');
  return {
    ...payment,
    order: raw.order ? {
      id: Number(raw.order.id),
      status: raw.order.status,
      date_ordered: raw.order.date_ordered,
    } : null,
  };
};
export const adaptPaymentDetail = (raw) => ({
  ...base(raw, 'payment-detail'),
  order: raw.order ? adaptOrderDetail(raw.order) : null,
});
export const adaptCheckoutSession = (raw) => {
  const data = requireObject(raw, 'checkout-session');
  const paymentUrl = String(data.checkout_url || '');
  let url;
  if (paymentUrl) {
    try { url = new URL(paymentUrl); } catch { throw new ApiContractError('checkout-session', 'checkout_url', paymentUrl); }
    const localMock = ['localhost', '127.0.0.1'].includes(url.hostname);
    const provider = String(data.provider || '');
    if (url.username || url.password) {
      throw new ApiContractError('checkout-session', 'checkout_url', paymentUrl);
    }
    if (url.protocol !== 'https:' && !(localMock && provider === 'mock' && url.protocol === 'http:')) {
      throw new ApiContractError('checkout-session', 'checkout_url', paymentUrl);
    }
    if (
      (provider === 'ligdicash' && url.hostname !== 'app.ligdicash.com')
      || (provider !== 'ligdicash' && !(provider === 'mock' && localMock))
    ) {
      throw new ApiContractError('checkout-session', 'checkout_url', paymentUrl);
    }
  }
  return {
    checkout_url: paymentUrl,
    payment_id: finiteInteger(requireField(data, 'payment_id', 'checkout-session'), 'checkout-session', 'payment_id'),
    order_id: finiteInteger(requireField(data, 'order_id', 'checkout-session'), 'checkout-session', 'order_id'),
    status: String(requireField(data, 'status', 'checkout-session')),
    provider: String(requireField(data, 'provider', 'checkout-session')),
    amount: String(requireField(data, 'amount', 'checkout-session')),
    currency: String(requireField(data, 'currency', 'checkout-session')),
    replayed: Boolean(data.replayed),
  };
};
