import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ProductCard from '../product/ProductCard';
import { Button, Card, Section } from '../ui';
import { getBestSellers } from '../../api/products';
import { logger } from '../../utils/logger';
import HomeReveal, { HomeRevealItem } from './HomeReveal';
import './ProductsSection.css';

const ProductsSection = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBestSellers = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getBestSellers();
        let products = data;
        
        // Limiter à 3 produits maximum
        if (products.length > 3) {
          products = products.slice(0, 3);
        }
        
        setProducts(products);
      } catch (err) {
        setError('Impossible de charger les best sellers');
        logger.error('Error fetching best sellers:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBestSellers();
  }, []);

  return (
    <Section
      className="products-section"
      animateTitle
      background="subtle"
      title="Best Sellers"
      subtitle="Nos créations les plus convoitées"
    >
        {loading ? (
          <div className="home-state products-loading" role="status">
            <span className="home-spinner" aria-hidden="true" />
            <p>Chargement des best sellers...</p>
          </div>
        ) : error ? (
          <Card className="home-state products-error">
            <p>{error}</p>
            <Button onClick={() => window.location.reload()}>
              Réessayer
            </Button>
          </Card>
        ) : products.length === 0 ? (
          <Card className="home-state products-empty">
            <p>Aucun best seller pour le moment.</p>
            <Link to="/shop" className="btn btn-outline btn-medium view-all-btn">
              Découvrir tous nos produits
            </Link>
          </Card>
        ) : (
          <HomeReveal className="products-grid" stagger>
            {products.map((product) => (
              <HomeRevealItem key={product.id} className="product-reveal-item">
                <ProductCard
                  id={product.id}
                  name={product.name}
                  price={product.price}
                  image={product.image}
                  variants={product.variants}
                  video={product.video}
                  badge={product.badge}
                  salesCount={product.sales_count}
                />
              </HomeRevealItem>
            ))}
          </HomeReveal>
        )}
    </Section>
  );
};

export default ProductsSection;
