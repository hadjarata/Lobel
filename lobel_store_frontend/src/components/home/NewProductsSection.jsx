import React, { useState, useEffect } from 'react';
import { ChevronDown, ShoppingBag } from 'lucide-react';
import ProductCard from '../product/ProductCard';
import { Button, Card, Section } from '../ui';
import { getNewProducts } from '../../api/products';
import { logger } from '../../utils/logger';
import HomeReveal, { HomeRevealItem } from './HomeReveal';
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
        const productsArray = data;
        setProducts(productsArray);
      } catch (err) {
        setError('Impossible de charger les nouveautés');
        logger.error('Error fetching new products:', err);
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
    <Section
      className="new-products-section"
      id="new-products"
      title="Nouveautés"
      subtitle="Les dernières pièces de notre sélection, pensées pour vous"
    >
        {loading ? (
          <div className="home-state new-products-loading" role="status">
            <span className="home-spinner" aria-hidden="true" />
            <p>Chargement des nouveautés...</p>
          </div>
        ) : error ? (
          <Card className="home-state new-products-error">
            <p>{error}</p>
            <Button onClick={() => window.location.reload()}>
              Réessayer
            </Button>
          </Card>
        ) : products.length === 0 ? (
          <Card className="home-state new-products-empty">
            <div className="empty-content">
              <ShoppingBag className="empty-icon" aria-hidden="true" />
              <h3 className="empty-title">Aucune nouveauté disponible pour le moment</h3>
              <p className="empty-subtitle">Revenez bientôt pour découvrir nos dernières collections</p>
              <Button type="button" onClick={() => window.location.assign('/shop')}>
                Voir la boutique
              </Button>
            </div>
          </Card>
        ) : (
          <>
            <HomeReveal className="new-arrivals-grid" stagger>
              {visibleProducts.map((product) => (
                <HomeRevealItem key={product.id} className="product-reveal-item">
                  <ProductCard
                    id={product.id}
                    name={product.name}
                    price={product.price}
                    image={product.image}
                    variants={product.variants}
                    video={product.video}
                    salesCount={product.sales_count}
                  />
                </HomeRevealItem>
              ))}
            </HomeReveal>

            {showToggle && (
              <div className="new-products-cta">
                <Button
                  type="button"
                  variant="outline"
                  className="view-all-new-btn"
                  onClick={() => setExpanded((prev) => !prev)}
                  aria-expanded={expanded}
                >
                  {expanded ? 'Réduire les nouveautés' : 'Afficher tous les nouveaux produits'}
                  <ChevronDown className={`cta-arrow${expanded ? ' is-expanded' : ''}`} aria-hidden="true" />
                </Button>
              </div>
            )}
          </>
        )}
    </Section>
  );
};

export default NewProductsSection;
