export const ORDER_STATUSES = {
  cart: { label: 'Panier', tone: 'neutral' },
  pending_payment: { label: 'En attente de paiement', tone: 'warning' },
  payment_processing: { label: 'Vérification du paiement', tone: 'warning' },
  payment_failed: { label: 'Paiement non confirmé', tone: 'danger' },
  paid: { label: 'Paiement confirmé', tone: 'success' },
  preparing: { label: 'En préparation', tone: 'info' },
  shipped: { label: 'Expédiée', tone: 'info' },
  delivered: { label: 'Livrée', tone: 'success' },
  cancelled: { label: 'Annulée', tone: 'neutral' },
  expired: { label: 'Expirée', tone: 'neutral' },
  refund_required: { label: 'Intervention requise', tone: 'danger' },
  refund_pending: { label: 'Remboursement en cours', tone: 'warning' },
  refunded: { label: 'Remboursée', tone: 'neutral' },
  refund_failed: { label: 'Remboursement à vérifier', tone: 'danger' },
};

export const getOrderStatus = (code) => ORDER_STATUSES[code] || {
  label: 'Statut en cours de mise à jour',
  tone: 'neutral',
};

export const isOrderPaymentConfirmed = (order) => (
  order?.payment?.status === 'completed'
  && ['paid', 'preparing', 'shipped', 'delivered', 'refund_pending', 'refunded']
    .includes(order?.status)
);
