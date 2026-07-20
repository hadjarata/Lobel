export const CATALOG_PAGE_SIZE = 24;

export const CATALOG_SORTS = Object.freeze({
  newest: '-date_created',
  oldest: 'date_created',
  price_asc: 'price',
  price_desc: '-price',
  name_asc: 'name',
  popular: '-sales_count',
});

export const DEFAULT_CATALOG_QUERY = Object.freeze({
  page: 1,
  search: '',
  sort: 'newest',
  category: null,
  collection: null,
  minPrice: null,
  maxPrice: null,
  color: null,
  size: null,
  available: null,
});

const positiveInteger = (value) => {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : null;
};

const nonNegativeDecimal = (value) => {
  if (value == null || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? String(value) : null;
};

export const parseCatalogQuery = (input) => {
  const params = input instanceof URLSearchParams ? input : new URLSearchParams(input);
  const available = params.get('available');
  return {
    page: positiveInteger(params.get('page')) || 1,
    search: (params.get('q') || '').trim().slice(0, 100),
    sort: Object.hasOwn(CATALOG_SORTS, params.get('sort')) ? params.get('sort') : 'newest',
    category: positiveInteger(params.get('category')),
    collection: params.get('collection')?.trim() || null,
    minPrice: nonNegativeDecimal(params.get('min_price')),
    maxPrice: nonNegativeDecimal(params.get('max_price')),
    color: positiveInteger(params.get('color')),
    size: positiveInteger(params.get('size')),
    available: available === 'true' ? true : available === 'false' ? false : null,
  };
};

export const serializeCatalogQuery = (query) => {
  const params = new URLSearchParams();
  if (query.page > 1) params.set('page', String(query.page));
  if (query.search) params.set('q', query.search);
  if (query.sort !== 'newest') params.set('sort', query.sort);
  if (query.category) params.set('category', String(query.category));
  if (query.collection) params.set('collection', query.collection);
  if (query.minPrice != null) params.set('min_price', String(query.minPrice));
  if (query.maxPrice != null) params.set('max_price', String(query.maxPrice));
  if (query.color) params.set('color', String(query.color));
  if (query.size) params.set('size', String(query.size));
  if (query.available != null) params.set('available', String(query.available));
  return params;
};

export const updateCatalogQuery = (query, patch, preservePage = false) => ({
  ...query,
  ...patch,
  page: preservePage ? (patch.page ?? query.page) : 1,
});

export const toProductListParams = (query) => {
  const params = {
    page: query.page,
    page_size: CATALOG_PAGE_SIZE,
    ordering: CATALOG_SORTS[query.sort],
  };
  if (query.search) params.search = query.search;
  if (query.category) params.category = query.category;
  if (query.collection) params.collection = query.collection;
  if (query.minPrice != null) params.min_price = query.minPrice;
  if (query.maxPrice != null) params.max_price = query.maxPrice;
  if (query.color) params.color = query.color;
  if (query.size) params.size = query.size;
  if (query.available != null) params.available = query.available;
  return params;
};

export const catalogPriceError = (query) => (
  query.minPrice != null && query.maxPrice != null
  && Number(query.minPrice) > Number(query.maxPrice)
    ? 'Le prix minimum doit être inférieur ou égal au prix maximum.'
    : null
);

export const totalCatalogPages = (count) => Math.max(1, Math.ceil(count / CATALOG_PAGE_SIZE));

