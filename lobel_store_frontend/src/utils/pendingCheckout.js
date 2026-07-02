const STORAGE_KEY = 'pendingCheckout';

export const savePendingCheckout = ({ paymentId, orderId, sessionToken = null }) => {
  const payload = {
    paymentId,
    orderId: orderId ?? null,
    sessionToken,
    createdAt: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
};

export const getPendingCheckout = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const data = JSON.parse(raw);
    if (data?.paymentId == null) {
      return null;
    }

    return data;
  } catch {
    return null;
  }
};

export const clearPendingCheckout = () => {
  localStorage.removeItem(STORAGE_KEY);
};
