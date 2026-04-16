import React from 'react';
import { Link } from 'react-router-dom';
import './ProductCard.css';

const ProductCard = ({ 
  id, 
  name, 
  price, 
  image, 
  video,
  category = '',
  badge = null 
}) => {
  return (
    <Link to={`/product/${id}`} className="product-card-link">
      <div className="product-card">
        <div className="product-image-container">
          {video ? (
            <video 
              src={video} 
              alt={name}
              className="product-video"
              autoPlay
              loop
              muted
              playsInline
            />
          ) : (
            <img 
              src={image} 
              alt={name}
              className="product-image"
              loading="lazy"
            />
          )}
          {badge && (
            <span className={`product-badge badge-${badge.type}`}>
              {badge.text}
            </span>
          )}
          <div className="product-overlay">
            <button className="view-product-btn">
              Voir le produit
            </button>
          </div>
        </div>
        
        <div className="product-info">
          {category && <span className="product-category">{category}</span>}
          <h3 className="product-name">{name}</h3>
          <div className="product-price-row">
            <span className="product-price">{price.toLocaleString()} FCFA</span>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
