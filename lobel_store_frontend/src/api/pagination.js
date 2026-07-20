import { ApiContractError, finiteInteger, requireObject } from './contracts/contract';

export const isPaginatedResponse = (value) => (
  Boolean(value) && typeof value === 'object' && !Array.isArray(value)
  && Object.prototype.hasOwnProperty.call(value, 'results')
);

export const adaptPagination = (value, itemAdapter = (item) => item) => {
  const data = requireObject(value, 'pagination');
  if (!Array.isArray(data.results)) throw new ApiContractError('pagination', 'results', data.results);
  const count = finiteInteger(data.count, 'pagination', 'count');
  if (count < 0) throw new ApiContractError('pagination', 'count', data.count);
  return {
    count,
    next: data.next == null ? null : String(data.next),
    previous: data.previous == null ? null : String(data.previous),
    results: data.results.map(itemAdapter),
  };
};

export const adaptUnpaginatedList = (value, itemAdapter = (item) => item) => {
  if (!Array.isArray(value)) throw new ApiContractError('unpaginated-list', 'response', value);
  return value.map(itemAdapter);
};

export const getResults = (page) => adaptPagination(page).results;

export const buildListParams = (filters = {}) => {
  const allowed = [
    'page', 'page_size', 'search', 'ordering', 'category', 'collection',
    'min_price', 'max_price', 'available', 'color', 'size', 'status', 'complete',
  ];
  return Object.fromEntries(allowed
    .filter((key) => filters[key] !== undefined && filters[key] !== null && filters[key] !== '')
    .map((key) => [key, filters[key]]));
};

