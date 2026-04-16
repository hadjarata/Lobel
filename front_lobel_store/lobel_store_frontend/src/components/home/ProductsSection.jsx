import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ProductCard from '../products/ProductCard';
import { getBestSellers } from '../../services/productService';
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
        const data = await getBestSellers(); // Utiliser l'endpoint bestsellers sans limite
        let products = data.results || data;
        
        // Limiter à 3 produits maximum
        if (products.length > 3) {
          products = products.slice(0, 3);
        }
        
        setProducts(products);
      } catch (err) {
        setError('Impossible de charger les best sellers');
        console.error('Error fetching best sellers:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBestSellers();
  }, []);

  return (
    <section className="products-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Best Sellers</h2>
          <p className="section-subtitle">
            Découvrez nos produits les plus vendus
          </p>
        </div>
        {loading ? (
          <div className="products-loading">
            <div className="loading-spinner"></div>
            <p>Chargement des best sellers...</p>
          </div>
        ) : error ? (
          <div className="products-error">
            <p>{error}</p>
            <button className="retry-btn" onClick={() => window.location.reload()}>
              Réessayer
            </button>
          </div>
        ) : products.length === 0 ? (
          <div className="products-empty">
            <p>Aucun best seller pour le moment.</p>
            <Link to="/shop" className="view-all-btn">
              Découvrir tous nos produits
            </Link>
          </div>
        ) : (
          <div className="products-grid">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                id={product.id}
                name={product.name}
                price={product.price}
                image={product.image}
                video={product.video}
                category={product.category?.name || product.category}
                badge={product.badge}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default ProductsSection;
