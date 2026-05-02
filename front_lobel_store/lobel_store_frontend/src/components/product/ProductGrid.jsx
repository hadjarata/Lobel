import React from 'react';
import ProductCard from './ProductCard';
import './ProductGrid.css';

const ProductGrid = ({ 
  products = [], 
  loading = false, 
  columns = 4,
  onProductClick 
}) => {
  if (loading) {
    return (
      <div className="product-grid-loading">
        {[...Array(8)].map((_, index) => (
          <div key={index} className="product-card-skeleton">
            <div className="skeleton-image"></div>
            <div className="skeleton-content">
              <div className="skeleton-title"></div>
              <div className="skeleton-price"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="product-grid-empty">
        <div className="empty-state">
          <div className="empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#FFB6C1" strokeWidth="1">
              <circle cx="9" cy="21" r="1"></circle>
              <circle cx="20" cy="21" r="1"></circle>
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
            </svg>
          </div>
          <h3 className="empty-title">Aucun produit trouvé</h3>
          <p className="empty-message">
            Essayez de modifier vos filtres pour voir plus de produits.
          </p>
        </div>
      </div>
    );
  }

  const gridClasses = `product-grid grid-${columns}-columns`;

  return (
    <div className={gridClasses}>
      {products.map((product) => (
        <ProductCard
          key={product.id}
          id={product.id}
          name={product.name}
          price={product.price}
          image={product.image}
          collections={product.collections}
          badge={product.badge}
          salesCount={product.sales_count}
          onClick={() => onProductClick && onProductClick(product)}
        />
      ))}
    </div>
  );
};

export default ProductGrid;
