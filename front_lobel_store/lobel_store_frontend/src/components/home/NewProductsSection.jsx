import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import ProductCard from '../products/ProductCard';
import { getNewProducts } from '../../api/products';
import './NewProductsSection.css';

const NewProductsSection = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    const fetchNewProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getNewProducts(); // Sans limite pour récupérer tous les nouveautés
        const productsArray = Array.isArray(data) ? data : [];
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
    const checkScrollButtons = () => {
      const container = scrollContainerRef.current;
      if (!container) return;

      const { scrollLeft, scrollWidth, clientWidth } = container;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    };

    const container = scrollContainerRef.current;
    if (container) {
      container.addEventListener('scroll', checkScrollButtons);
      checkScrollButtons(); // Vérifier au montage
    }

    return () => {
      if (container) {
        container.removeEventListener('scroll', checkScrollButtons);
      }
    };
  }, [products]);

  const scrollLeft = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

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
              <Link to="/shop" className="view-shop-btn">
                Voir la boutique
              </Link>
            </div>
          </div>
        ) : (
          <>
            <div className="new-products-carousel-container">
              <button 
                className={`carousel-arrow carousel-arrow-left ${!canScrollLeft ? 'disabled' : ''}`}
                onClick={scrollLeft}
                disabled={!canScrollLeft}
                aria-label="Défiler à gauche"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>

              <div className="new-products-scroll-container">
                <div 
                  ref={scrollContainerRef}
                  className={`new-products-scroll ${products.length <= 3 ? 'few-products' : ''}`}
                >
                  {products.map((product) => (
                    <div key={product.id} className="product-card-wrapper">
                      <ProductCard
                        id={product.id}
                        name={product.name}
                        price={product.price}
                        image={product.image}
                        video={product.video}
                        category={product.category?.name || product.category}
                        badge={product.badge}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <button 
                className={`carousel-arrow carousel-arrow-right ${!canScrollRight ? 'disabled' : ''}`}
                onClick={scrollRight}
                disabled={!canScrollRight}
                aria-label="Défiler à droite"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>
            
            <div className="new-products-cta">
              <Link to="/shop?filter=new" className="view-all-btn">
                Voir toutes les nouveautés
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
};

export default NewProductsSection;
