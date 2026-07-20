export const PAYMENT_FINAL_STATUSES = new Set([
  'completed', 'failed', 'cancelled', 'expired',
]);

export const isPaymentFinal = (status) => PAYMENT_FINAL_STATUSES.has(status);

export const paymentPollDelay = (attempt) => (
  Math.min(2000 * (2 ** Math.max(0, attempt)), 15000)
);

export const safePaymentReturnPath = () => '/checkout/payment/return';

export const canRedirectPayment = (session, orderId) => Boolean(
  session
  && session.order_id === orderId
  && ['ligdicash', 'mock'].includes(session.provider)
  && session.status === 'redirect_required'
  && session.checkout_url,
);
