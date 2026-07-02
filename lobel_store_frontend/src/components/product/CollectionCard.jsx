import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './CollectionCard.css';

const BACKEND_BASE_URL = 'http://127.0.0.1:8000';

const normalizeMediaUrl = (url) => {
  if (!url) {
    return null;
  }

  if (
    url.startsWith('http://') ||
    url.startsWith('https://') ||
    url.startsWith('data:') ||
    url.startsWith('blob:')
  ) {
    return url;
  }

  return `${BACKEND_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`;
};

const CollectionCard = ({
  title,
  subtitle,
  image,
  video,
  products = [],
  link = '/shop'
}) => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const hasProducts = products && products.length > 0;

  const mediaItems = hasProducts
    ? products
        .map((product) => ({
          type: product.video ? 'video' : 'image',
          src: normalizeMediaUrl(product.video || product.image),
          alt: product.name,
          productId: product.id,
        }))
        .filter((item) => item.src)
    : [
        {
          type: video ? 'video' : image ? 'image' : 'default',
          src: normalizeMediaUrl(video || image),
          alt: title,
          productId: null,
        },
      ];

  useEffect(() => {
    if (!hasProducts || mediaItems.length <= 1) return;

    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % mediaItems.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [hasProducts, mediaItems.length]);

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  const renderSingleCover = () => {
    const cover = mediaItems[0];

    if (cover?.type === 'video' && cover.src) {
      return (
        <video
          src={cover.src}
          className="carousel-media"
          autoPlay
          muted
          loop
          playsInline
        />
      );
    }

    if (cover?.type === 'image' && cover.src) {
      return (
        <img
          src={cover.src}
          alt={cover.alt}
          className="carousel-media"
        />
      );
    }

    return (
      <div className="collection-empty-background">
        <div className="collection-empty-pattern"></div>
      </div>
    );
  };

  return (
    <div className="collection-card">
      <div className="collection-carousel-container">
        {hasProducts && mediaItems.length > 0 ? (
          <>
            <div className="collection-carousel">
              {mediaItems.map((item, index) => (
                <div
                  key={`${item.productId ?? 'cover'}-${index}`}
                  className={`carousel-slide ${index === currentSlide ? 'active' : ''}`}
                >
                  {item.type === 'video' ? (
                    <video
                      src={item.src}
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
          renderSingleCover()
        )}

        <div className="collection-overlay">
          <div className="collection-content">
            <h3 className="collection-title">{title}</h3>
            {subtitle && <p className="collection-subtitle">{subtitle}</p>}
            {!hasProducts && (
              <p className="collection-empty-message">
                Les produits de cette collection arrivent bientot.
              </p>
            )}
            <Link to={link} className="collection-link">
              {hasProducts ? 'Voir la collection' : 'Decouvrir bientot'}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionCard;
