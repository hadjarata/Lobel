import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './CollectionCard.css';

const CollectionCard = ({ 
  title, 
  subtitle, 
  image, 
  products = [],
  link = '/shop' 
}) => {
  const [currentSlide, setCurrentSlide] = useState(0);

  // Déterminer si la collection a des produits
  const hasProducts = products && products.length > 0;

  // Préparer les médias (images et vidéos) pour le carousel
  const mediaItems = hasProducts 
    ? products.map(product => ({
        type: product.video ? 'video' : 'image',
        src: product.video || product.image,
        alt: product.name,
        productId: product.id
      }))
    : [{
        type: 'default',
        src: null,
        alt: title,
        productId: null
      }];

  // Défilement automatique uniquement pour les collections avec produits
  useEffect(() => {
    if (!hasProducts || mediaItems.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % mediaItems.length);
    }, 3000); // Change toutes les 3 secondes

    return () => clearInterval(interval);
  }, [hasProducts, mediaItems.length]);

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  return (
    <div className="collection-card">
      <div className="collection-carousel-container">
        {hasProducts ? (
          // CAS : COLLECTION AVEC PRODUITS - Carousel des médias
          <>
            <div className="collection-carousel">
              {mediaItems.map((item, index) => (
                <div
                  key={index}
                  className={`carousel-slide ${index === currentSlide ? 'active' : ''}`}
                >
                  {item.type === 'video' ? (
                    <video
                      src={item.src}
                      alt={item.alt}
                      className="carousel-media"
                      autoPlay
                      muted
                      loop
                      playsInline
                    />
                  ) : (
                    <img
                      src={item.src}
                      alt={item.alt}
                      className="carousel-media"
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Indicateurs du carousel */}
            {mediaItems.length > 1 && (
              <div className="carousel-indicators">
                {mediaItems.map((_, index) => (
                  <button
                    key={index}
                    className={`indicator ${index === currentSlide ? 'active' : ''}`}
                    onClick={() => goToSlide(index)}
                    aria-label={`Aller au slide ${index + 1}`}
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          // CAS : COLLECTION VIDE - Fond visuel par défaut
          <div className="collection-empty-background">
            <div className="collection-empty-pattern"></div>
          </div>
        )}

        {/* Overlay avec informations */}
        <div className="collection-overlay">
          <div className="collection-content">
            <h3 className="collection-title">{title}</h3>
            {subtitle && <p className="collection-subtitle">{subtitle}</p>}
            {!hasProducts && (
              <p className="collection-empty-message">
                Les produits de cette collection arrivent bientôt.
              </p>
            )}
            <Link to={link} className="collection-link">
              {hasProducts ? 'Voir la collection' : 'Découvrir bientôt'}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionCard;
