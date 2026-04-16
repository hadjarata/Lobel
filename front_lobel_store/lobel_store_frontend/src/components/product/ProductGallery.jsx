import React, { useState, useRef, useEffect } from 'react';
import './ProductGallery.css';

const ProductGallery = ({ media, productName }) => {
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);
  const mainMediaRef = useRef(null);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  const currentMedia = media[currentMediaIndex];

  // Gestion du swipe mobile
  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    if (!touchStartX.current || !touchEndX.current) return;
    
    const diff = touchStartX.current - touchEndX.current;
    const threshold = 50;

    if (Math.abs(diff) > threshold) {
      if (diff > 0 && currentMediaIndex < media.length - 1) {
        // Swipe gauche - média suivant
        setCurrentMediaIndex(currentMediaIndex + 1);
      } else if (diff < 0 && currentMediaIndex > 0) {
        // Swipe droit - média précédent
        setCurrentMediaIndex(currentMediaIndex - 1);
      }
    }

    touchStartX.current = 0;
    touchEndX.current = 0;
  };

  // Navigation au clavier
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft' && currentMediaIndex > 0) {
        setCurrentMediaIndex(currentMediaIndex - 1);
      } else if (e.key === 'ArrowRight' && currentMediaIndex < media.length - 1) {
        setCurrentMediaIndex(currentMediaIndex + 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentMediaIndex, media.length]);

  // Gestion du zoom
  const handleMediaClick = () => {
    if (currentMedia.type === 'image') {
      setIsZoomed(!isZoomed);
    }
  };

  const selectMedia = (index) => {
    setCurrentMediaIndex(index);
    setIsZoomed(false);
  };

  const nextMedia = () => {
    if (currentMediaIndex < media.length - 1) {
      setCurrentMediaIndex(currentMediaIndex + 1);
      setIsZoomed(false);
    }
  };

  const prevMedia = () => {
    if (currentMediaIndex > 0) {
      setCurrentMediaIndex(currentMediaIndex - 1);
      setIsZoomed(false);
    }
  };

  if (!media || media.length === 0) {
    return (
      <div className="product-gallery-empty">
        <p>Aucun média disponible</p>
      </div>
    );
  }

  return (
    <div className="product-gallery">
      {/* Média principal */}
      <div className="main-media-container">
        <div 
          className={`main-media ${isZoomed ? 'zoomed' : ''}`}
          onClick={handleMediaClick}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          {currentMedia.type === 'image' ? (
            <img
              ref={mainMediaRef}
              src={currentMedia.url}
              alt={`${productName} - ${currentMediaIndex + 1}`}
              className="main-image"
              loading="eager"
            />
          ) : (
            <video
              ref={mainMediaRef}
              src={currentMedia.url}
              alt={`${productName} - ${currentMediaIndex + 1}`}
              className="main-video"
              autoPlay
              loop
              muted
              playsInline
              controls={false}
            />
          )}
        </div>

        {/* Navigation desktop */}
        {media.length > 1 && (
          <>
            <button 
              className="nav-btn prev-btn"
              onClick={prevMedia}
              disabled={currentMediaIndex === 0}
              aria-label="Média précédent"
            >
              ‹
            </button>
            <button 
              className="nav-btn next-btn"
              onClick={nextMedia}
              disabled={currentMediaIndex === media.length - 1}
              aria-label="Média suivant"
            >
              ›
            </button>
          </>
        )}

        {/* Indicateur de type média */}
        <div className="media-indicator">
          {currentMedia.type === 'video' ? (
            <span className="video-indicator">▶</span>
          ) : (
            <span className="image-indicator">📷</span>
          )}
        </div>

        {/* Indicateur de progression */}
        {media.length > 1 && (
          <div className="progress-indicator">
            {currentMediaIndex + 1} / {media.length}
          </div>
        )}
      </div>

      {/* Thumbnails */}
      {media.length > 1 && (
        <div className="thumbnails-container">
          <div className="thumbnails">
            {media.map((item, index) => (
              <button
                key={index}
                className={`thumbnail ${index === currentMediaIndex ? 'active' : ''}`}
                onClick={() => selectMedia(index)}
                aria-label={`Média ${index + 1}`}
              >
                {item.type === 'image' ? (
                  <img
                    src={item.url}
                    alt={`${productName} - ${index + 1}`}
                    className="thumbnail-image"
                    loading="lazy"
                  />
                ) : (
                  <div className="thumbnail-video">
                    <video
                      src={item.url}
                      className="thumbnail-video-player"
                      muted
                      loop
                      playsInline
                    />
                    <div className="thumbnail-video-overlay">
                      <span>▶</span>
                    </div>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Overlay pour le zoom */}
      {isZoomed && (
        <div className="zoom-overlay" onClick={() => setIsZoomed(false)}>
          <div className="zoomed-image-container">
            {currentMedia.type === 'image' && (
              <img
                src={currentMedia.url}
                alt={`${productName} - Zoom`}
                className="zoomed-image"
              />
            )}
          </div>
          <button className="zoom-close" onClick={() => setIsZoomed(false)}>
            ✕
          </button>
        </div>
      )}
    </div>
  );
};

export default ProductGallery;
