import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getCatalogFilterOptions } from '../../api/products';
import {
  parseCatalogQuery,
  serializeCatalogQuery,
  totalCatalogPages,
  updateCatalogQuery,
} from '../../catalog/catalogQuery';
import { useCatalogProducts } from '../../catalog/useCatalogProducts';
import ProductGrid from '../../components/product/ProductGrid';
import FilterSidebar from '../../components/ui/FilterSidebar';
import Pagination from '../../components/ui/Pagination';
import { normalizeApiError } from '../../utils/apiErrors';
import './Shop.css';

const EMPTY_OPTIONS = { categories: [], collections: [], colors: [], sizes: [], price: {} };
const MotionDiv = motion.div;

const Shop = () => {
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = useMemo(() => parseCatalogQuery(searchParams), [searchParams]);
  const [searchInput, setSearchInput] = useState(query.search);
  const [options, setOptions] = useState(EMPTY_OPTIONS);
  const [optionsError, setOptionsError] = useState(null);
  const [retryKey, setRetryKey] = useState(0);
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);
  const searchTimer = useRef(null);
  const resultsHeading = useRef(null);
  const state = useCatalogProducts(query, retryKey);
  const totalPages = totalCatalogPages(state.count);

  const commitQuery = useCallback((patch, { preservePage = false, replace = false } = {}) => {
    setSearchParams(
      serializeCatalogQuery(updateCatalogQuery(query, patch, preservePage)),
      { replace },
    );
  }, [query, setSearchParams]);

  useEffect(() => {
    const canonical = serializeCatalogQuery(query).toString();
    if (searchParams.toString() !== canonical) setSearchParams(canonical, { replace: true });
  }, [query, searchParams, setSearchParams]);

  useEffect(() => {
    const timer = window.setTimeout(() => setSearchInput(query.search), 0);
    return () => window.clearTimeout(timer);
  }, [query.search]);

  useEffect(() => {
    if (searchInput === query.search) return undefined;
    searchTimer.current = window.setTimeout(
      () => commitQuery({ search: searchInput }, { replace: true }),
      350,
    );
    return () => window.clearTimeout(searchTimer.current);
  }, [commitQuery, query.search, searchInput]);

  useEffect(() => {
    const controller = new AbortController();
    getCatalogFilterOptions({ signal: controller.signal })
      .then((value) => {
        setOptions(value);
        setOptionsError(null);
      })
      .catch((error) => {
        const normalized = normalizeApiError(error, 'Impossible de charger les filtres.');
        if (!normalized.isCanceled) setOptionsError(normalized.message);
      });
    return () => controller.abort();
  }, [retryKey]);

  useEffect(() => {
    const resize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  useEffect(() => {
    if (!state.loading && state.count > 0 && query.page > totalPages) {
      commitQuery({ page: totalPages }, { preservePage: true, replace: true });
    }
  }, [commitQuery, query.page, state.count, state.loading, totalPages]);

  const submitSearch = (event) => {
    event.preventDefault();
    window.clearTimeout(searchTimer.current);
    commitQuery({ search: searchInput });
  };

  const changeFilter = (name, value) => {
    commitQuery({ [name]: value });
    if (isMobile) setIsMobileFilterOpen(false);
  };

  const changePage = (page) => {
    commitQuery({ page }, { preservePage: true });
    window.requestAnimationFrame(() => resultsHeading.current?.focus());
  };

  const clearFilters = () => {
    setSearchInput('');
    setSearchParams('');
  };

  const activeFilters = [
    query.search, query.category, query.collection, query.minPrice, query.maxPrice,
    query.color, query.size, query.available,
  ].filter((value) => value !== null && value !== '').length;
  const activeCollection = options.collections.find(({ slug }) => slug === query.collection);

  return (
    <main className="shop">
      <header className="shop-header">
        <div className="shop-header-content">
          <span className="shop-eyebrow">LobelStore · Sélection</span>
          <h1 className="shop-title">{activeCollection?.name || 'Boutique'}</h1>
          <p className="shop-subtitle">
            {activeCollection
              ? `Explorez la collection ${activeCollection.name}`
              : 'Découvrez notre collection complète de vêtements féminins'}
          </p>
          <form className="catalog-search" role="search" onSubmit={submitSearch}>
            <label className="sr-only" htmlFor="catalog-search">Rechercher un produit</label>
            <input
              id="catalog-search"
              type="search"
              value={searchInput}
              maxLength={100}
              placeholder="Nom, catégorie, collection ou référence…"
              onChange={(event) => setSearchInput(event.target.value)}
            />
            <button type="submit">
              <Search aria-hidden="true" />
              <span>Rechercher</span>
            </button>
          </form>
          {isMobile && (
            <button
              type="button"
              className="filter-toggle-btn"
              aria-expanded={isMobileFilterOpen}
              aria-controls="mobile-catalog-filters"
              onClick={() => setIsMobileFilterOpen(true)}
            >
              <SlidersHorizontal aria-hidden="true" />
              Filtres {activeFilters > 0 && <span className="filter-count">{activeFilters}</span>}
            </button>
          )}
        </div>
      </header>

      <div className="shop-content">
        {!isMobile && (
          <aside className="shop-sidebar" aria-label="Filtres du catalogue">
            <FilterSidebar
              query={query}
              options={options}
              onChange={changeFilter}
              onClear={clearFilters}
            />
          </aside>
        )}

        <section className="shop-main" aria-busy={state.loading}>
          <div className="catalog-toolbar">
            <h2 ref={resultsHeading} tabIndex="-1">
              {state.loading ? 'Chargement…' : `${state.count} produit${state.count > 1 ? 's' : ''}`}
            </h2>
            {activeFilters > 0 && (
              <button type="button" className="catalog-clear" onClick={clearFilters}>
                Réinitialiser les filtres
              </button>
            )}
          </div>
          <div className="sr-only" role="status" aria-live="polite">
            {state.loading ? 'Chargement des produits' : `${state.count} résultats chargés`}
          </div>
          {(state.error || optionsError) && (
            <div className="shop-error" role="alert">
              <p>{state.error || optionsError}</p>
              <button type="button" onClick={() => setRetryKey((key) => key + 1)} className="retry-btn">
                Réessayer
              </button>
            </div>
          )}
          {!state.loading && !state.error && state.products.length === 0 ? (
            <div className="catalog-empty">
              <p>Aucun produit ne correspond à ces critères.</p>
              <button type="button" onClick={clearFilters}>Effacer les filtres</button>
            </div>
          ) : (
            <MotionDiv
              className="shop-grid-reveal"
              key={serializeCatalogQuery(query).toString()}
              initial={reducedMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reducedMotion ? 0 : 0.28, ease: [0.2, 0, 0, 1] }}
            >
              <ProductGrid
                products={state.products}
                loading={state.loading}
                columns={4}
                onProductClick={(product) => navigate(`/product/${product.id}`)}
              />
            </MotionDiv>
          )}
          {!state.loading && !state.error && state.count > 0 && (
            <Pagination
              currentPage={query.page}
              totalPages={totalPages}
              onPageChange={changePage}
            />
          )}
        </section>
      </div>

      {isMobile && (
        <FilterSidebar
          id="mobile-catalog-filters"
          query={query}
          options={options}
          onChange={changeFilter}
          onClear={clearFilters}
          isMobile
          isOpen={isMobileFilterOpen}
          onClose={() => setIsMobileFilterOpen(false)}
        />
      )}
    </main>
  );
};

export default Shop;
