import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { springTap } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './ProductCard.css';

const MotionButton = motion.button;

const ProductCard = ({ id, name, price, image, video, badge, rating, reviewCount }) => {
  const navigate = useNavigate();
  const tapTransition = useMotionTransition(springTap);
  const numericPrice = Number(price);
  const displayPrice = Number.isFinite(numericPrice)
    ? numericPrice.toLocaleString('fr-FR', { maximumFractionDigits: 2 })
    : '—';
  const stars = rating ? '★'.repeat(Math.round(rating)) : null;

  const openDetail = (event) => {
    event.preventDefault();
    event.stopPropagation();
    navigate(`/product/${id}`);
  };

  return (
    <article className="product-card">
      <Link to={`/product/${id}`} className="product-card-link">
        <div className="product-image-container">
          {badge && <span className="product-badge">{badge}</span>}
          {video ? (
            <video src={video} className="product-video" muted playsInline preload="metadata" controls />
          ) : (
            <img src={image} alt={name} className="product-image" loading="lazy" />
          )}
        </div>
      </Link>
      <div className="product-card-body">
        <Link to={`/product/${id}`} className="product-card-link">
          <h3 className="product-card-title">{name}</h3>
        </Link>
        <div className="product-card-footer">
          <div>
            <span className="product-card-price">{displayPrice} FCFA</span>
            {(rating || reviewCount != null) && (
              <div className="product-card-rating">
                {stars && <span className="product-rating-stars">{stars}</span>}
                {reviewCount != null && <span className="product-review-count">({reviewCount})</span>}
              </div>
            )}
          </div>
          <MotionButton type="button" className="product-add-button" onClick={openDetail}
            aria-label={`Choisir les options de ${name}`} title="Choisir les options"
            whileTap={{ scale: 0.92 }} transition={tapTransition}>
            <svg className="cart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="9" cy="21" r="1" />
              <circle cx="20" cy="21" r="1" />
              <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
            </svg>
          </MotionButton>
        </div>
      </div>
    </article>
  );
};

export default ProductCard;
