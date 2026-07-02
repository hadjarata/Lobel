import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getProducts, getCollections, getCategories } from '../../api/products';
import ProductGrid from '../../components/product/ProductGrid';
import FilterSidebar from '../../components/ui/FilterSidebar';
import Pagination from '../../components/ui/Pagination';
import {
  filterProductsByCollectionSlug,
  normalizeApiList,
} from '../../utils/collectionUtils';
import './Shop.css';

const Shop = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [collections, setCollections] = useState([]);
  const [categories, setCategories] = useState([]);
  const [colors, setColors] = useState([]);
  const [sizes, setSizes] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState(() => {
    const collectionSlug = new URLSearchParams(window.location.search).get('collection');
    return collectionSlug ? { collection: collectionSlug } : {};
  });
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    const collectionSlug = searchParams.get('collection');
    setFilters((prev) => {
      if (collectionSlug) {
        if (prev.collection === collectionSlug) {
          return prev;
        }
        return { ...prev, collection: collectionSlug };
      }

      if (!prev.collection) {
        return prev;
      }

      const next = { ...prev };
      delete next.collection;
      return next;
    });
  }, [searchParams]);

  const syncCollectionParam = useCallback(
    (collectionSlug) => {
      const nextParams = new URLSearchParams(searchParams);

      if (collectionSlug) {
        nextParams.set('collection', collectionSlug);
      } else {
        nextParams.delete('collection');
      }

      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const applyFilters = useCallback(() => {
    let filteredProducts = [...allProducts];

    if (filters.collection) {
      filteredProducts = filterProductsByCollectionSlug(
        filteredProducts,
        collections,
        filters.collection,
      );

      if (import.meta.env.DEV) {
        console.info('[Shop] collection filter', {
          collection: filters.collection,
          totalProducts: allProducts.length,
          matchedProducts: filteredProducts.length,
        });
      }
    }

    if (filters.category) {
      filteredProducts = filteredProducts.filter(
        (product) =>
          product.category?.id === filters.category ||
          product.category === filters.category,
      );
    }

    if (filters.color?.length > 0) {
      filteredProducts = filteredProducts.filter((product) =>
        product.variants?.some((variant) =>
          filters.color.some(
            (color) => variant.color?.name === color || variant.color === color,
          ),
        ),
      );
    }

    if (filters.size?.length > 0) {
      filteredProducts = filteredProducts.filter((product) =>
        product.variants?.some((variant) =>
          filters.size.some(
            (size) => variant.size?.name === size || variant.size === size,
          ),
        ),
      );
    }

    if (filters.price) {
      filteredProducts = filteredProducts.filter(
        (product) =>
          Number(product.price) >= filters.price.min &&
          Number(product.price) <= filters.price.max,
      );
    }

    if (filters.isNew) {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      filteredProducts = filteredProducts.filter(
        (product) => new Date(product.date_created) >= thirtyDaysAgo,
      );
    }

    setProducts(filteredProducts);
  }, [allProducts, collections, filters]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [productsResponse, collectionsResponse, categoriesResponse] =
        await Promise.all([getProducts(), getCollections(), getCategories()]);

      const productsData = normalizeApiList(productsResponse);
      const collectionsData = normalizeApiList(collectionsResponse);
      const categoriesData = normalizeApiList(categoriesResponse);

      setAllProducts(productsData);
      setCollections(collectionsData);
      setCategories(categoriesData);
      extractColorsAndSizes(productsData);
    } catch (fetchError) {
      console.error('Error fetching initial data:', fetchError);
      setError('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const extractColorsAndSizes = (productsList) => {
    const uniqueColors = new Set();
    const uniqueSizes = new Set();

    productsList.forEach((product) => {
      product.variants?.forEach((variant) => {
        if (variant.color) {
          uniqueColors.add(variant.color.name || variant.color);
        }
        if (variant.size) {
          uniqueSizes.add(variant.size.name || variant.size);
        }
      });
    });

    setColors(Array.from(uniqueColors));
    setSizes(Array.from(uniqueSizes));
  };

  const handleFilterChange = (filterType, value) => {
    if (filterType === 'clear') {
      setFilters({});
      setCurrentPage(1);
      syncCollectionParam(null);
      return;
    }

    if (filterType === 'collection') {
      const nextCollection = filters.collection === value ? null : value;
      syncCollectionParam(nextCollection);
      setFilters((prev) => {
        const newFilters = { ...prev };
        if (nextCollection) {
          newFilters.collection = nextCollection;
        } else {
          delete newFilters.collection;
        }
        return newFilters;
      });
      setCurrentPage(1);
      return;
    }

    setFilters((prev) => {
      const newFilters = { ...prev };

      if (filterType === 'category') {
        newFilters.category = prev.category === value ? null : value;
      } else if (filterType === 'price') {
        newFilters.price = prev.price?.label === value.label ? null : value;
      } else if (filterType === 'size') {
        const currentSizes = prev.size || [];
        if (currentSizes.includes(value)) {
          newFilters.size = currentSizes.filter((s) => s !== value);
          if (newFilters.size.length === 0) {
            delete newFilters.size;
          }
        } else {
          newFilters.size = [...currentSizes, value];
        }
      } else if (filterType === 'color') {
        const currentColors = prev.color || [];
        if (currentColors.includes(value)) {
          newFilters.color = currentColors.filter((c) => c !== value);
          if (newFilters.color.length === 0) {
            delete newFilters.color;
          }
        } else {
          newFilters.color = [...currentColors, value];
        }
      } else if (filterType === 'isNew') {
        newFilters.isNew = !prev.isNew;
      }

      return newFilters;
    });
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleProductClick = (product) => {
    navigate(`/product/${product.id}`);
  };

  const getGridColumns = () => {
    if (window.innerWidth <= 480) return 1;
    if (window.innerWidth <= 768) return 2;
    if (window.innerWidth <= 1024) return 3;
    return 4;
  };

  const hasActiveFilters = Object.keys(filters).length > 0;
  const activeCollection = collections.find(
    (collection) => collection.slug === filters.collection,
  );

  return (
    <div className="shop">
      <div className="shop-header">
        <div className="shop-header-content">
          <h1 className="shop-title">
            {activeCollection ? activeCollection.name : 'Boutique'}
          </h1>
          <p className="shop-subtitle">
            {activeCollection
              ? `Explorez la collection ${activeCollection.name}`
              : 'Découvrez notre collection complète de vêtements féminins'}
          </p>
        </div>

        {isMobile && (
          <div className="mobile-filter-toggle">
            <button
              className="filter-toggle-btn"
              onClick={() => setIsMobileFilterOpen(true)}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="4" y1="21" x2="4" y2="14"></line>
                <line x1="4" y1="10" x2="4" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12" y2="3"></line>
                <line x1="20" y1="21" x2="20" y2="16"></line>
                <line x1="20" y1="12" x2="20" y2="3"></line>
                <line x1="1" y1="14" x2="7" y2="14"></line>
                <line x1="9" y1="8" x2="15" y2="8"></line>
                <line x1="17" y1="16" x2="23" y2="16"></line>
              </svg>
              Filtres
              {hasActiveFilters && (
                <span className="filter-count">
                  {Object.values(filters).filter((v) =>
                    Array.isArray(v) ? v.length > 0 : v !== null,
                  ).length}
                </span>
              )}
            </button>
          </div>
        )}
      </div>

      <div className="shop-content">
        {!isMobile && (
          <div className="shop-sidebar">
            <FilterSidebar
              filters={filters}
              onFilterChange={handleFilterChange}
              isMobile={false}
              collections={collections}
              categories={categories}
              colors={colors}
              sizes={sizes}
            />
          </div>
        )}

        <div className="shop-main">
          {error && (
            <div className="shop-error">
              <p>{error}</p>
              <button onClick={fetchInitialData} className="retry-btn">
                Réessayer
              </button>
            </div>
          )}

          <ProductGrid
            products={products}
            loading={loading}
            columns={getGridColumns()}
            onProductClick={handleProductClick}
          />

          {!loading && !error && products.length > 0 && totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </div>
      </div>

      {isMobile && (
        <FilterSidebar
          filters={filters}
          onFilterChange={handleFilterChange}
          isMobile={true}
          isOpen={isMobileFilterOpen}
          onClose={() => setIsMobileFilterOpen(false)}
          collections={collections}
          categories={categories}
          colors={colors}
          sizes={sizes}
        />
      )}
    </div>
  );
};

export default Shop;
