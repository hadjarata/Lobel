export const ENDPOINTS = {

  // =========================
  // AUTH
  // =========================
  LOGIN: "/api/auth/login/",
  REFRESH_TOKEN: "/api/auth/refresh/",
  LOGOUT: "/api/auth/logout/",
  CURRENT_USER: "/api/users/customers/me/",
  CHANGE_PASSWORD: "/api/users/customers/change-password/",
  VERIFY_EMAIL: "/api/users/customers/verify-email/",
  PASSWORD_RESET_REQUEST: "/api/users/customers/request-password-reset/",
  PASSWORD_RESET_CONFIRM: "/api/users/customers/reset-password/",

  // REGISTER (🔥 AJOUT IMPORTANT)
  REGISTER: "/api/users/customers/",

  // =========================
  // PRODUCTS
  // =========================
  PRODUCTS: "/api/products/products/",
  PRODUCT_DETAIL: (id) => `/api/products/products/${encodeURIComponent(id)}/`,
  NEW_PRODUCTS: "/api/products/products/new/",
  BESTSELLERS: "/api/products/products/bestsellers/",
  PRODUCT_FILTER_OPTIONS: "/api/products/products/filter-options/",
  RESOLVE_VARIANTS: "/api/products/products/resolve-variants/",

  // Categories
  CATEGORIES: "/api/products/categories/",
  CATEGORY_DETAIL: (id) => `/api/products/categories/${encodeURIComponent(id)}/`,

  // Mapping collections
  COLLECTIONS: "/api/products/collections/",
  COLLECTION_DETAIL: (slug) => `/api/products/collections/${encodeURIComponent(slug)}/`,

  // =========================
  // ORDERS
  // =========================
  ORDERS: "/api/orders/orders/",
  CART: "/api/orders/orders/cart/",
  CART_MERGE: "/api/orders/orders/cart/merge/",
  CART_CLEAR: "/api/orders/orders/cart/clear/",
  CHECKOUT_DELIVERY_OPTIONS: "/api/orders/orders/checkout/delivery-options/",
  CHECKOUT_PREVIEW: "/api/orders/orders/checkout/preview/",
  CHECKOUT_CREATE_ORDER: "/api/orders/orders/checkout/create-order/",
  CHECKOUT_PENDING: "/api/orders/orders/checkout/pending/",
  ORDER_DETAIL: (id) => `/api/orders/orders/${encodeURIComponent(id)}/`,
  ORDER_CANCEL: (id) => `/api/orders/orders/${encodeURIComponent(id)}/cancel/`,
  ORDER_RECEIPT: (id) => `/api/orders/orders/${encodeURIComponent(id)}/receipt/`,

  ORDER_ITEMS: "/api/orders/order-items/",
  ORDER_ITEM_DETAIL: (id) => `/api/orders/order-items/${encodeURIComponent(id)}/`,

  // =========================
  // PAYMENTS
  // =========================
  PAYMENTS: "/api/payments/payments/",
  PAYMENT_DETAIL: (id) => `/api/payments/payments/${encodeURIComponent(id)}/`,
  CHECKOUT: "/api/payments/checkout/",
  PAYMENT_REFRESH: (id) => `/api/payments/payments/${encodeURIComponent(id)}/refresh-status/`,
  PAYMENT_REDIRECTED: (id) => `/api/payments/payments/${encodeURIComponent(id)}/redirected/`,
  MOCK_CONFIRM: "/api/payments/mock/confirm/",

  // =========================
  // USERS
  // =========================
  CUSTOMERS: "/api/users/customers/",
  CUSTOMER_DETAIL: (id) => `/api/users/customers/${encodeURIComponent(id)}/`,
};
