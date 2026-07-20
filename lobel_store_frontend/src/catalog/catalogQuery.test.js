import { describe, expect, it } from 'vitest';
import {
  CATALOG_PAGE_SIZE,
  catalogPriceError,
  parseCatalogQuery,
  serializeCatalogQuery,
  toProductListParams,
  totalCatalogPages,
  updateCatalogQuery,
} from './catalogQuery';

describe('catalog query contract', () => {
  const parsingCases = [
    ['', 'page', 1],
    ['page=3', 'page', 3],
    ['page=0', 'page', 1],
    ['page=-2', 'page', 1],
    ['page=hello', 'page', 1],
    ['q=robe', 'search', 'robe'],
    ['q=%20robe%20', 'search', 'robe'],
    ['sort=price_asc', 'sort', 'price_asc'],
    ['sort=price_desc', 'sort', 'price_desc'],
    ['sort=name_asc', 'sort', 'name_asc'],
    ['sort=popular', 'sort', 'popular'],
    ['sort=unknown', 'sort', 'newest'],
    ['category=7', 'category', 7],
    ['category=0', 'category', null],
    ['category=text', 'category', null],
    ['collection=ete', 'collection', 'ete'],
    ['collection=%20', 'collection', null],
    ['min_price=10.50', 'minPrice', '10.50'],
    ['min_price=-1', 'minPrice', null],
    ['min_price=x', 'minPrice', null],
    ['max_price=30', 'maxPrice', '30'],
    ['max_price=-2', 'maxPrice', null],
    ['color=4', 'color', 4],
    ['color=-1', 'color', null],
    ['size=9', 'size', 9],
    ['size=no', 'size', null],
    ['available=true', 'available', true],
    ['available=false', 'available', false],
    ['available=1', 'available', null],
  ];

  it.each(parsingCases)('parse %s => %s=%s', (input, field, expected) => {
    expect(parseCatalogQuery(input)[field]).toBe(expected);
  });

  const serializationCases = [
    [{ page: 2 }, 'page=2'],
    [{ search: 'robe' }, 'q=robe'],
    [{ sort: 'price_asc' }, 'sort=price_asc'],
    [{ category: 3 }, 'category=3'],
    [{ collection: 'fete' }, 'collection=fete'],
    [{ minPrice: '5' }, 'min_price=5'],
    [{ maxPrice: '10' }, 'max_price=10'],
    [{ color: 4 }, 'color=4'],
    [{ size: 5 }, 'size=5'],
    [{ available: true }, 'available=true'],
    [{ available: false }, 'available=false'],
  ];

  it.each(serializationCases)('serializes %o', (patch, fragment) => {
    const params = serializeCatalogQuery({ ...parseCatalogQuery(''), ...patch });
    expect(params.toString()).toContain(fragment);
  });

  it('omits defaults from canonical URL', () => {
    expect(serializeCatalogQuery(parseCatalogQuery('')).toString()).toBe('');
  });

  it('round-trips a complete query', () => {
    const raw = 'page=2&q=robe&sort=popular&category=3&collection=ete&min_price=5&max_price=50&color=2&size=4&available=true';
    expect(parseCatalogQuery(serializeCatalogQuery(parseCatalogQuery(raw)))).toEqual(parseCatalogQuery(raw));
  });

  it('resets the page when a filter changes', () => {
    expect(updateCatalogQuery({ ...parseCatalogQuery(''), page: 8 }, { color: 2 }).page).toBe(1);
  });

  it('preserves an explicit page navigation', () => {
    expect(updateCatalogQuery(parseCatalogQuery(''), { page: 4 }, true).page).toBe(4);
  });

  it('maps all fields to the API vocabulary', () => {
    expect(toProductListParams(parseCatalogQuery(
      'page=2&q=x&sort=price_desc&category=3&collection=c&min_price=1&max_price=9&color=4&size=5&available=true',
    ))).toEqual({
      page: 2, page_size: CATALOG_PAGE_SIZE, ordering: '-price', search: 'x',
      category: 3, collection: 'c', min_price: '1', max_price: '9',
      color: 4, size: 5, available: true,
    });
  });

  it.each([
    [0, 1], [1, 1], [24, 1], [25, 2], [48, 2], [49, 3], [240, 10],
  ])('calculates pages for %i products', (count, expected) => {
    expect(totalCatalogPages(count)).toBe(expected);
  });

  it('rejects an inverted price interval', () => {
    expect(catalogPriceError({ minPrice: '20', maxPrice: '10' })).toMatch(/minimum/);
  });

  it('accepts equal price bounds', () => {
    expect(catalogPriceError({ minPrice: '10', maxPrice: '10' })).toBeNull();
  });

  it('accepts a partial price interval', () => {
    expect(catalogPriceError({ minPrice: null, maxPrice: '10' })).toBeNull();
  });

  it('limits search input to the API maximum', () => {
    expect(parseCatalogQuery(`q=${'a'.repeat(120)}`).search).toHaveLength(100);
  });
});

