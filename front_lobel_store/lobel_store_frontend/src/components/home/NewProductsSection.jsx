import React, { useState, useEffect } from 'react';
import ProductCard from '../product/ProductCard';
import { getNewProducts } from '../../api/products';
import './NewProductsSection.css';

const getColumnCount = (width) => {
  if (width >= 1024) return 4;
  if (width >= 768) return 3;
  return 2;
};

const NewProductsSection = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [columns, setColumns] = useState(getColumnCount(window.innerWidth));

  useEffect(() => {
    const fetchNewProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getNewProducts();
        const productsArray = Array.isArray(data) ? data : data?.results || [];
        setProducts(productsArray);
      } catch (err) {
        setError('Impossible de charger les nouveautés');
        console.error('Error fetching new products:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNewProducts();
  }, []);

  useEffect(() => {
    const handleResize = () => setColumns(getColumnCount(window.innerWidth));
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const visibleProducts = expanded ? products : products.slice(0, columns);
  const showToggle = products.length > columns;

  return (
    <section className="new-products-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Nouveautés</h2>
          <p className="section-subtitle">
            Découvrez nos dernières arrivées et tendances du moment
          </p>
        </div>

        {loading ? (
          <div className="new-products-loading">
            <div className="loading-spinner"></div>
            <p>Chargement des nouveautés...</p>
          </div>
        ) : error ? (
          <div className="new-products-error">
            <p>{error}</p>
            <button className="retry-btn" onClick={() => window.location.reload()}>
              Réessayer
            </button>
          </div>
        ) : products.length === 0 ? (
          <div className="new-products-empty">
            <div className="empty-content">
              <div className="empty-icon">?</div>
              <h3 className="empty-title">Aucune nouveauté disponible pour le moment</h3>
              <p className="empty-subtitle">Revenez bientôt pour découvrir nos dernières collections</p>
              <button className="view-shop-btn" type="button" onClick={() => window.location.assign('/shop')}>
                Voir la boutique
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="new-arrivals-grid">
              {visibleProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  id={product.id}
                  name={product.name}
                  price={product.price}
                  image={product.image}
                  video={product.video}
                />
              ))}
            </div>

            {showToggle && (
              <div className="new-products-cta">
                <button
                  type="button"
                  className="view-all-new-btn"
                  onClick={() => setExpanded((prev) => !prev)}
                  aria-expanded={expanded}
                >
                  {expanded ? 'Réduire les nouveautés' : 'Afficher tous les nouveaux produits'}
                  <svg className="cta-arrow" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M7 10l5 5 5-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
};

export default NewProductsSection;
