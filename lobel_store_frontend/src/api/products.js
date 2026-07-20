import api from './axios';
import { ENDPOINTS } from './endpoints';
import { adaptPagination, buildListParams } from './pagination';
import {
  adaptCategory,
  adaptCollection,
  adaptProductDetail,
  adaptProductListItem,
} from './contracts/catalog';

const getProductPage = (endpoint, filters = {}, requestConfig = {}) => api.get(endpoint, {
  ...requestConfig,
  params: buildListParams(filters),
}).then(({ data }) => adaptPagination(data, adaptProductListItem));

export const getProducts = (filters = {}, requestConfig = {}) => getProductPage(
  ENDPOINTS.PRODUCTS, filters, requestConfig,
);
export const getProductById = (id, requestConfig = {}) => api.get(
  ENDPOINTS.PRODUCT_DETAIL(id), requestConfig,
)
  .then(({ data }) => adaptProductDetail(data));
export const getBestSellers = (limit = 4) => getProductPage(
  ENDPOINTS.BESTSELLERS,
  { page_size: limit },
).then(({ results }) => results);
export const getNewProducts = (limit) => getProductPage(
  ENDPOINTS.NEW_PRODUCTS,
  limit ? { page_size: limit } : {},
).then(({ results }) => results);
export const getCategories = (filters = {}) => api.get(ENDPOINTS.CATEGORIES, {
  params: buildListParams(filters),
}).then(({ data }) => adaptPagination(data, adaptCategory));
export const getProductsByCategory = (categoryId, filters = {}) => getProductPage(
  ENDPOINTS.PRODUCTS,
  { ...filters, category: categoryId },
);
export const getCollections = (filters = {}) => api.get(ENDPOINTS.COLLECTIONS, {
  params: buildListParams(filters),
}).then(({ data }) => adaptPagination(data, adaptCollection));
export const getProductsByCollection = (collection, filters = {}) => getProductPage(
  ENDPOINTS.PRODUCTS,
  { ...filters, collection },
);
export const searchProducts = (search, filters = {}) => getProductPage(
  ENDPOINTS.PRODUCTS,
  { ...filters, search },
);

export const getCatalogFilterOptions = (requestConfig = {}) => api.get(
  ENDPOINTS.PRODUCT_FILTER_OPTIONS,
  requestConfig,
).then(({ data }) => data);
