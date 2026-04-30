import React from 'react';
import { Link } from 'react-router-dom';
import './ProductCard.css';

const ProductCard = ({ id, name, price, image, video }) => {
  return (
    <Link to={`/product/${id}`} className="product-card-link">
      <div className="product-card">
        <div className="product-image-container">
          {video ? (
            <video
              src={video}
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
        </div>

        <div className="product-info">
          <h3 className="product-name">{name}</h3>
          <span className="product-price">{price.toLocaleString()} FCFA</span>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
