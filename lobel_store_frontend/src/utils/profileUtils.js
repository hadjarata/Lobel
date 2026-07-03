export const normalizeApiList = (data) => {
  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data?.results)) {
    return data.results;
  }

  return [];
};

export const formatPrice = (value) =>
  Number(value || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });

export const formatDate = (value) => {
  if (!value) {
    return '—';
  }

  return new Date(value).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export const formatDateTime = (value) => {
  if (!value) {
    return '—';
  }

  return new Date(value).toLocaleString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const ORDER_STATUS_LABELS = {
  pending: 'En attente',
  paid: 'Payée',
  failed: 'Échouée',
  cancelled: 'Annulée',
  refunded: 'Remboursée',
};

export const PAYMENT_STATUS_LABELS = {
  pending: 'En attente',
  completed: 'Confirmé',
  failed: 'Échoué',
};

export const PAYMENT_METHOD_LABELS = {
  card: 'Carte bancaire',
  paypal: 'PayPal',
  cash: 'Espèces',
  mock: 'Mode test',
  ligdicash: 'LigdiCash',
};

export const getOrderStatusLabel = (status) =>
  ORDER_STATUS_LABELS[status] || status || 'Inconnu';

export const getPaymentStatusLabel = (status) =>
  PAYMENT_STATUS_LABELS[status] || status || 'Inconnu';

export const getPaymentMethodLabel = (method) =>
  PAYMENT_METHOD_LABELS[method] || method || '—';

export const getCustomerDisplayName = (customer) => {
  const firstName = customer?.user?.first_name || '';
  const lastName = customer?.user?.last_name || '';
  const fullName = `${firstName} ${lastName}`.trim();

  if (fullName) {
    return fullName;
  }

  return customer?.user?.email || customer?.user?.username || 'Client';
};

export const getCustomerInitials = (customer) => {
  const name = getCustomerDisplayName(customer);
  const parts = name.split(' ').filter(Boolean);

  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }

  return name.slice(0, 2).toUpperCase();
};

export const getAccountStatus = (customer) => {
  const isActive = customer?.user?.is_active ?? true;
  return isActive
    ? { label: 'Compte actif', tone: 'success' }
    : { label: 'Compte inactif', tone: 'warning' };
};
