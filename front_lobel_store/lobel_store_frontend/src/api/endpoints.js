export const ENDPOINTS = {

// =========================
// AUTH
// =========================
LOGIN: "/api/token/",
REFRESH_TOKEN: "/api/token/refresh/",
LOGOUT: "/api/logout/",
CURRENT_USER: "/api/users/me/",
CHANGE_PASSWORD: "/api/users/change-password/",

// =========================
// PRODUCTS
// =========================

// Products
PRODUCTS: "/api/products/products/",
PRODUCT_DETAIL: (id) => `/api/products/products/${id}/`,
NEW_PRODUCTS: "/api/products/products/new/",
BESTSELLERS: "/api/products/products/bestsellers/",

// Categories (Collections côté frontend)
CATEGORIES: "/api/products/categories/",
CATEGORY_DETAIL: (id) => `/api/products/categories/${id}/`,

// Collections
COLLECTIONS: "/api/products/collections/",
COLLECTION_DETAIL: (id) => `/api/products/collections/${id}/`,
COLLECTION_PRODUCTS: (id) => `/api/products/collections/${id}/products/`,
CATEGORY_PRODUCTS: (id) => `/api/products/categories/${id}/products/`,

// =========================
// ORDERS
// =========================

// Orders
ORDERS: "/api/orders/orders/",
ORDER_DETAIL: (id) => `/api/orders/orders/${id}/`,

// Order Items
ORDER_ITEMS: "/api/orders/order-items/",
ORDER_ITEM_DETAIL: (id) => `/api/orders/order-items/${id}/`,

// =========================
// PAYMENTS
// =========================

PAYMENTS: "/api/payments/payments/",
PAYMENT_DETAIL: (id) => `/api/payments/payments/${id}/`,

// =========================
// USERS / CUSTOMERS
// =========================

CUSTOMERS: "/api/users/customers/",
CUSTOMER_DETAIL: (id) => `/api/users/customers/${id}/`

};
