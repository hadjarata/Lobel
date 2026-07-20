export const categoryFixture = {
  id: 3, name: 'Robes', description: 'Collection robes', is_active: true,
  date_created: '2026-01-10T12:00:00Z',
};
export const collectionFixture = {
  id: 4, name: 'Été', slug: 'ete', description: '', cover_type: 'image',
  image: '/media/collections/ete.jpg', image_url: 'http://testserver/media/collections/ete.jpg',
  video: null, video_url: null, is_active: true, start_date: null, end_date: null,
  products: [11], created_at: '2026-01-10T12:00:00Z', updated_at: '2026-01-10T12:00:00Z',
};
export const variantFixture = {
  id: 21, color: { id: 1, name: 'Noir', hex_code: '#000000' },
  size: { id: 2, name: 'M' }, stock: 5, is_active: true, sku: 'ROB-M-NOIR', price: '15000.00',
};
export const productListFixture = {
  id: 11, name: 'Robe noire', price: '15000.00', sales_count: 2,
  date_created: '2026-01-10T12:00:00Z', category: categoryFixture,
  collections: [4], variants: [variantFixture],
  image: 'http://testserver/media/products/11/main.jpg', is_available: true,
};
export const productDetailFixture = {
  ...productListFixture, description: 'Description', is_active: true,
  media_files: [{
    id: 31, media_type: 'image', url: 'http://testserver/media/products/11/main.jpg',
    order: 0, width: 800, height: 1000, duration_seconds: null,
  }],
  video: null,
};
export const customerFixture = {
  id: 7,
  user: {
    id: 9, username: 'client@example.test', first_name: 'Awa', last_name: 'Diallo',
    email: 'client@example.test', is_active: true,
  },
  country: 'ML', phone_number: '+22370000000', address: 'Bamako',
  date_created: '2026-01-10T12:00:00Z',
};
export const orderItemFixture = {
  id: 41, product_id: 11, product_reference: 'prod-ref', product_name: 'Robe noire',
  variant_id: 21, variant_reference: 'variant-ref', variant_name: 'Noir / M',
  color: 'Noir', size: 'M', sku: 'ROB-M-NOIR', quantity: 2,
  unit_price: '15000.00', currency: 'XOF', discount_amount: '0.00',
  subtotal: '30000.00', line_total: '30000.00', date_added: '2026-01-10T12:00:00Z',
};
export const orderListFixture = {
  id: 51, date_ordered: '2026-01-10T12:00:00Z', complete: true, status: 'paid',
  cart_total: '30000.00', cart_items: 2, total_amount: '30000.00', currency: 'XOF',
};
export const orderDetailFixture = {
  ...orderListFixture, customer: customerFixture, items: [orderItemFixture],
  status_history: [], paid_at: '2026-01-10T12:05:00Z', transaction_id: 'TX-TEST',
};
export const emptyCartFixture = {
  id: null, items: [], cart_total: 0, cart_items: 0, complete: false, status: 'pending',
};
export const paymentListFixture = {
  id: 61, order: { id: 51, status: 'paid', date_ordered: '2026-01-10T12:00:00Z' },
  amount: '30000.00', payment_method: 'ligdicash', status: 'completed',
  provider: 'ligdicash', currency: 'XOF', processed_at: '2026-01-10T12:05:00Z',
  date_paid: '2026-01-10T12:01:00Z',
};
export const paymentDetailFixture = {
  ...paymentListFixture, order: orderDetailFixture, session_token: 'fixture-session',
  order_reference: 'ORDER-51', external_transaction_id: 'EXT-TEST',
};
export const pageFixture = (results) => ({
  count: results.length, next: null, previous: null, results,
});

