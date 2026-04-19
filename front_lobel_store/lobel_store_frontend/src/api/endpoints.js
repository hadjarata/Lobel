export const ENDPOINTS = {

  // =========================
  // AUTH
  // =========================
  LOGIN: "/api/token/",
  REFRESH_TOKEN: "/api/token/refresh/",
  LOGOUT: "/api/logout/", // ⚠️ vérifier backend (sinon inutile)
  CURRENT_USER: "/api/users/customers/me/",
  CHANGE_PASSWORD: "/api/users/change-password/",

  // REGISTER (🔥 AJOUT IMPORTANT)
  REGISTER: "/api/users/customers/",

  // =========================
  // PRODUCTS
  // =========================
  PRODUCTS: "/api/products/products/",
  PRODUCT_DETAIL: (id) => `/api/products/products/${id}/`,
  NEW_PRODUCTS: "/api/products/products/new/",
  BESTSELLERS: "/api/products/products/bestsellers/",

  // Categories
  CATEGORIES: "/api/products/categories/",
  CATEGORY_DETAIL: (id) => `/api/products/categories/${id}/`,

  // Mapping collections
  COLLECTIONS: "/api/products/categories/",
  COLLECTION_DETAIL: (id) => `/api/products/categories/${id}/`,
  CATEGORY_PRODUCTS: (id) => `/api/products/products/?category=${id}`,

  // =========================
  // ORDERS
  // =========================
  ORDERS: "/api/orders/orders/",
  ORDER_DETAIL: (id) => `/api/orders/orders/${id}/`,

  ORDER_ITEMS: "/api/orders/order-items/",
  ORDER_ITEM_DETAIL: (id) => `/api/orders/order-items/${id}/`,

  // =========================
  // PAYMENTS
  // =========================
  PAYMENTS: "/api/payments/payments/",
  PAYMENT_DETAIL: (id) => `/api/payments/payments/${id}/`,

  // =========================
  // USERS
  // =========================
  CUSTOMERS: "/api/users/customers/",
  CUSTOMER_DETAIL: (id) => `/api/users/customers/${id}/`,
};