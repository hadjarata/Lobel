export const formatPrice = (value) => {
  if (value === null || value === undefined || value === '') return '—';
  const amount = Number(value);
  return Number.isFinite(amount)
    ? amount.toLocaleString('fr-FR', { maximumFractionDigits: 2 })
    : '—';
};

export const formatDate = (value) => {
  if (!value) {
    return '—';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export const formatDateTime = (value) => {
  if (!value) {
    return '—';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('fr-FR', {
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
