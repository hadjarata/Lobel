import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { addOrderItem } from '../../api/cart';
import { toast } from '../../components/ui/toast';
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
      toast.success('Produit ajouté au panier');
    } catch (error) {
      toast.error('Erreur lors de l\'ajout au panier');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <article className="product-card">
      <Link to={`/product/${id}`} className="product-card-link">
        <div className="product-image-container">
          {badge && <span className="product-badge">{badge}</span>}
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
      </Link>

      <div className="product-info">
        <h3 className="product-name">{name}</h3>
        
        <div className="product-price-section">
          <span className="product-price">{displayPrice} FCFA</span>
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

      <button
        type="button"
        className="product-add-button"
        onClick={handleAddToCart}
        aria-label="Ajouter au panier"
        disabled={isAdding}
        title="Ajouter au panier"
      >
        <svg className="cart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="9" cy="21" r="1" />
          <circle cx="20" cy="21" r="1" />
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
        </svg>
      </button>
    </article>
  );
};

export default ProductCard;
