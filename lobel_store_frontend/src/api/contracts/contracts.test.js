import { describe, expect, it } from 'vitest';
import { ENDPOINTS } from '../endpoints';
import { adaptPagination, adaptUnpaginatedList, buildListParams, isPaginatedResponse } from '../pagination';
import { normalizeApiError } from '../../utils/apiErrors';
import { adaptCategory, adaptCollection, adaptMedia, adaptProductDetail, adaptProductListItem } from './catalog';
import { adaptCustomer } from './customer';
import { adaptCart, adaptOrderDetail, adaptOrderItem, adaptOrderListItem } from './orders';
import { adaptCheckoutSession, adaptPaymentDetail, adaptPaymentListItem } from './payments';
import { ApiContractError } from './contract';
import {
  categoryFixture, collectionFixture, customerFixture, emptyCartFixture,
  orderDetailFixture, orderItemFixture, orderListFixture, pageFixture,
  paymentDetailFixture, paymentListFixture, productDetailFixture, productListFixture,
} from '../../test/fixtures/apiContracts';

describe('pagination DRF', () => {
  it('adapte une page valide', () => expect(adaptPagination(pageFixture([categoryFixture])).count).toBe(1));
  it('détecte une page', () => expect(isPaginatedResponse(pageFixture([]))).toBe(true));
  it('refuse results absent', () => expect(() => adaptPagination({ count: 0 })).toThrow(ApiContractError));
  it('refuse results non tableau', () => expect(() => adaptPagination({ count: 0, results: {} })).toThrow(ApiContractError));
  it('refuse count invalide', () => expect(() => adaptPagination({ count: 'x', results: [] })).toThrow(ApiContractError));
  it('distingue une liste non paginée', () => expect(adaptUnpaginatedList([categoryFixture])).toHaveLength(1));
  it('refuse un tableau comme page DRF', () => expect(() => adaptPagination([])).toThrow(ApiContractError));
});

describe('catalogue', () => {
  it('adapte un produit de liste', () => expect(adaptProductListItem(productListFixture).id).toBe(11));
  it('préserve le prix décimal', () => expect(adaptProductListItem(productListFixture).price).toBe('15000.00'));
  it('préserve un prix nul sans faux zéro', () => expect(adaptProductListItem({ ...productListFixture, price: null }).price).toBeNull());
  it('adapte le détail', () => expect(adaptProductDetail(productDetailFixture).description).toBe('Description'));
  it('expose les variantes stables', () => expect(adaptProductDetail(productDetailFixture).variants[0].id).toBe(21));
  it('adapte media.url', () => expect(adaptMedia(productDetailFixture.media_files[0]).url).toContain('/media/products/'));
  it('refuse le nom absent', () => {
    const invalid = { ...productListFixture };
    delete invalid.name;
    expect(() => adaptProductListItem(invalid)).toThrow(ApiContractError);
  });
  it('conserve un produit inactif', () => expect(adaptProductDetail({ ...productDetailFixture, is_active: false }).is_active).toBe(false));
  it('adapte une catégorie', () => expect(adaptCategory(categoryFixture).name).toBe('Robes'));
  it('tolère une description optionnelle', () => expect(adaptCategory({ ...categoryFixture, description: null }).description).toBe(''));
  it('adapte une collection', () => expect(adaptCollection(collectionFixture).slug).toBe('ete'));
  it('refuse un slug absent', () => {
    const invalid = { ...collectionFixture };
    delete invalid.slug;
    expect(() => adaptCollection(invalid)).toThrow(ApiContractError);
  });
});

describe('profil', () => {
  it('adapte /customers/me/', () => expect(adaptCustomer(customerFixture).user.email).toBe('client@example.test'));
  it('normalise les champs optionnels', () => expect(adaptCustomer({ ...customerFixture, address: null }).address).toBe(''));
  it('refuse user absent', () => {
    const invalid = { ...customerFixture };
    delete invalid.user;
    expect(() => adaptCustomer(invalid)).toThrow(ApiContractError);
  });
  it('adapte une réponse de mise à jour', () => expect(adaptCustomer({ ...customerFixture, address: 'Ségou' }).address).toBe('Ségou'));
});

describe('commandes et panier', () => {
  it('adapte une commande de liste sans lignes', () => expect(adaptOrderListItem(orderListFixture).items).toBeUndefined());
  it('adapte un détail avec lignes', () => expect(adaptOrderDetail(orderDetailFixture).items).toHaveLength(1));
  it('préserve les snapshots', () => expect(adaptOrderItem(orderItemFixture).product_name).toBe('Robe noire'));
  it('préserve les montants', () => expect(adaptOrderItem(orderItemFixture).line_total).toBe('30000.00'));
  it('adapte une variante de ligne', () => expect(adaptOrderItem(orderItemFixture).variant.id).toBe(21));
  it('adapte un panier vide', () => expect(adaptCart(emptyCartFixture).items).toEqual([]));
  it('adapte un panier avec lignes', () => expect(adaptCart(orderDetailFixture).cart_items).toBe(2));
  it('refuse un prix unitaire absent', () => {
    const invalid = { ...orderItemFixture };
    delete invalid.unit_price;
    expect(() => adaptOrderItem(invalid)).toThrow(ApiContractError);
  });
  it('refuse une quantité invalide', () => expect(() => adaptOrderItem({ ...orderItemFixture, quantity: 0 })).toThrow());
});

describe('paiements', () => {
  it('adapte une liste', () => expect(adaptPaymentListItem(paymentListFixture).order.id).toBe(51));
  it('adapte un détail', () => expect(adaptPaymentDetail(paymentDetailFixture).order.items).toHaveLength(1));
  it('adapte une session checkout HTTPS', () => {
    const value = adaptCheckoutSession({
      checkout_url: 'https://app.ligdicash.com/pay/session',
      payment_id: 61, order_id: 51, status: 'redirect_required',
      provider: 'ligdicash', amount: '1000.00', currency: 'XOF',
    });
    expect(value.payment_id).toBe(61);
  });
  it('refuse une URL de redirection invalide', () => expect(() => adaptCheckoutSession({
    checkout_url: 'javascript:alert(1)', payment_id: 1, order_id: 1,
    status: 'redirect_required', provider: 'ligdicash', amount: '1', currency: 'XOF',
  })).toThrow(ApiContractError));
  it('refuse un statut inconnu', () => expect(() => adaptPaymentListItem({
    ...paymentListFixture, status: 'mystery',
  })).toThrow(ApiContractError));
});

describe('erreurs API', () => {
  it('normalise detail', () => expect(normalizeApiError({ response: { status: 404, data: { detail: 'x' } } }).status).toBe(404));
  it('normalise les champs', () => expect(normalizeApiError({ response: { status: 400, data: { quantity: ['Invalide'] } } }).fieldErrors.quantity).toBe('Invalide'));
  it('normalise non_field_errors', () => expect(normalizeApiError({ response: { status: 400, data: { non_field_errors: ['Conflit'] } } }).nonFieldErrors).toEqual(['Conflit']));
  it('lit Retry-After', () => expect(normalizeApiError({ response: { status: 429, data: {}, headers: { 'retry-after': '10' } } }).retryAfter).toBe('10'));
  it('distingue le réseau', () => expect(normalizeApiError(new Error()).code).toBe('network_error'));
  it('distingue timeout', () => expect(normalizeApiError({ code: 'ECONNABORTED' }).code).toBe('timeout'));
  it('distingue annulation', () => expect(normalizeApiError({ code: 'ERR_CANCELED' }).isCanceled).toBe(true));
  it('distingue contrat', () => expect(normalizeApiError(new ApiContractError('x', 'y', {})).code).toBe('contract_error'));
});

describe('endpoints et query params', () => {
  it('utilise les chemins réels', () => expect(ENDPOINTS.CART).toBe('/api/orders/orders/cart/'));
  it('encode les segments', () => expect(ENDPOINTS.COLLECTION_DETAIL('été / 26')).toContain('%C3%A9t%C3%A9%20%2F%2026'));
  it('ne contient pas ancien logout', () => expect(Object.values(ENDPOINTS)).not.toContain('/api/logout/'));
  it('ne produit pas de double slash', () => expect(ENDPOINTS.PRODUCT_DETAIL(1)).not.toContain('//'));
  it('construit seulement les filtres backend', () => expect(buildListParams({
    page: 2, page_size: 10, search: 'robe', invented: true,
  })).toEqual({ page: 2, page_size: 10, search: 'robe' }));
});
