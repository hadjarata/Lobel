import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { addOrderItem, fetchCart } from '../../api/cart';
import './ProductCard.css';

const ProductCard = ({
  id,
  name,
  price,
  image,
  video,
  badge,
  salesCount,
  rating,
  reviewCount,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const { requireAuth } = useAuth();
  const displayPrice = Number(price || 0).toLocaleString('fr-FR', {
    maximumFractionDigits: 0,
  });
  const soldLabel = salesCount != null ? `${salesCount}+ sold` : null;
  const stars = rating ? '★'.repeat(Math.round(rating)) : null;

  const handleAddToCart = async (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (!requireAuth()) {
      return;
    }

    setIsAdding(true);

    try {
      await addOrderItem({
        product_id: id,
        quantity: 1,
      });
      await fetchCart();
      alert('Produit ajouté au panier');
    } catch (error) {
      console.error('Erreur ajout panier:', error);
      alert('Erreur lors de l\'ajout au panier');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <article className="product-card">
      <Link to={`/product/${id}`} className="product-card-link">
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
          <div className="product-info-top">
            {badge && <span className="product-badge">{badge}</span>}
            <h3 className="product-name">{name}</h3>
          </div>

          <div className="product-price-block">
            <span className="product-price">{displayPrice} FCFA</span>
            {soldLabel && <span className="product-sold">{soldLabel}</span>}
          </div>

          {(rating || reviewCount) && (
            <div className="product-rating-row">
              {stars && <span className="product-rating-stars">{stars}</span>}
              {reviewCount != null && (
                <span className="product-review-count">({reviewCount})</span>
              )}
            </div>
          )}
        </div>
      </Link>

      <button
        type="button"
        className="product-add-button"
        onClick={handleAddToCart}
        aria-label="Ajouter au panier"
        disabled={isAdding}
      >
        🛒
      </button>
    </article>
  );
};

export default ProductCard;
