import { finiteInteger, nullableString, requireField, requireObject } from './contract';
import { adaptCustomer } from './customer';

export const adaptOrderItem = (raw) => {
  const data = requireObject(raw, 'order-item');
  const quantity = finiteInteger(requireField(data, 'quantity', 'order-item'), 'order-item', 'quantity');
  if (quantity < 1) throw new TypeError('order-item: quantity doit être positive.');
  const unitPrice = requireField(data, 'unit_price', 'order-item');
  return {
    ...data,
    id: finiteInteger(requireField(data, 'id', 'order-item'), 'order-item', 'id'),
    product_id: data.product_id == null ? null : Number(data.product_id),
    variant_id: data.variant_id == null ? null : Number(data.variant_id),
    product_name: nullableString(data.product_name),
    variant_name: nullableString(data.variant_name),
    quantity,
    unit_price: unitPrice == null ? null : String(unitPrice),
    line_total: data.line_total == null ? null : String(data.line_total),
    subtotal: data.subtotal == null ? null : String(data.subtotal),
    currency: nullableString(data.currency) || 'XOF',
    product: {
      id: data.product_id == null ? null : Number(data.product_id),
      name: nullableString(data.product_name),
      price: unitPrice == null ? null : String(unitPrice),
    },
    variant: data.variant_id == null ? null : {
      id: Number(data.variant_id),
      name: nullableString(data.variant_name),
      sku: nullableString(data.sku),
      color: nullableString(data.color),
      size: nullableString(data.size),
    },
  };
};

const adaptOrderSummary = (raw, adapter) => {
  const data = requireObject(raw, adapter);
  return {
    ...data,
    id: finiteInteger(requireField(data, 'id', adapter), adapter, 'id'),
    date_ordered: nullableString(requireField(data, 'date_ordered', adapter)),
    complete: Boolean(requireField(data, 'complete', adapter)),
    status: String(requireField(data, 'status', adapter)),
    cart_total: data.cart_total == null ? null : String(data.cart_total),
    cart_items: finiteInteger(requireField(data, 'cart_items', adapter), adapter, 'cart_items'),
    total_amount: data.total_amount == null ? null : String(data.total_amount),
    currency: nullableString(data.currency) || 'XOF',
  };
};

export const adaptOrderListItem = (raw) => adaptOrderSummary(raw, 'order-list');
export const adaptOrderDetail = (raw) => {
  const order = adaptOrderSummary(raw, 'order-detail');
  return {
    ...order,
    customer: raw.customer ? adaptCustomer(raw.customer) : null,
    items: Array.isArray(raw.items) ? raw.items.map(adaptOrderItem) : [],
    status_history: Array.isArray(raw.status_history) ? raw.status_history : [],
    timeline: Array.isArray(raw.timeline) ? raw.timeline : [],
    available_actions: requireObject(raw.available_actions || {}, 'order-actions'),
    payment: raw.payment && typeof raw.payment === 'object' ? raw.payment : null,
    status_label: nullableString(raw.status_label),
  };
};

export const adaptCart = (raw) => {
  const data = requireObject(raw, 'cart');
  if (data.id === null) {
    if (!Array.isArray(data.items)) throw new TypeError('cart: items doit être un tableau.');
    return { ...data, items: [], cart_total: String(data.cart_total ?? '0'), cart_items: 0 };
  }
  return adaptOrderDetail(data);
};
