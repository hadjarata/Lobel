import { normalizeApiError } from '../utils/apiErrors';
const messages = {
  invalid_variant: 'Cette variante n’est plus disponible.',
  inactive_variant: 'Cette variante est indisponible.',
  inactive_product: 'Ce produit est indisponible.',
  insufficient_stock: 'La quantité demandée dépasse le stock disponible.',
  invalid_quantity: 'La quantité doit être un nombre entier valide.',
  idempotency_conflict: 'La synchronisation du panier est en conflit.',
};
export const normalizeCartError = (error) => {
  const normalized = normalizeApiError(error, 'Le panier est momentanément indisponible.');
  const raw = error?.response?.data?.code;
  const code = Array.isArray(raw) ? raw[0] : raw || normalized.code;
  return {
    ...normalized, code, message: messages[code] || normalized.message,
    availableQuantity: error?.response?.data?.available_quantity ?? null,
  };
};
