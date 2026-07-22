import React, { useState, useRef, useEffect } from 'react';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import {
  backdropVariants,
  springModal,
  springSnappy,
  zoomModalVariants,
} from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import { logger } from '../../utils/logger';
import './ProductGallery.css';

const ProductGallery = ({ media, productName, controls = null }) => {
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);
  const mainMediaRef = useRef(null);
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  // S'assurer que l'index est valide quand les médias changent
  useEffect(() => {
    if (media && media.length > 0 && currentMediaIndex >= media.length) {
      const timeoutId = window.setTimeout(() => setCurrentMediaIndex(0), 0);
      return () => window.clearTimeout(timeoutId);
    }
    return undefined;
  }, [media, currentMediaIndex]);

  const currentMedia = media && media.length > 0 ? media[currentMediaIndex] : null;

  // Filtrer les médias valides (double sécurité)
  const validMedia = media ? media.filter(m => m.url && typeof m.url === 'string') : [];

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
    if (currentMediaIndex < validMedia.length - 1) {
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

  const overlayTransition = useMotionTransition(springModal);
  const zoomTransition = useMotionTransition(springSnappy);

  if (!validMedia || validMedia.length === 0) {
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
              loading="lazy"
              style={{ objectFit: 'cover' }}
              onError={(e) => {
                logger.warn('Erreur de chargement image:', currentMedia.url);
                e.target.style.display = 'none';
              }}
            />
          ) : currentMedia.type === 'video' ? (
            <video
              ref={mainMediaRef}
              src={currentMedia.url}
              alt={`${productName} - ${currentMediaIndex + 1}`}
              className="main-video"
              autoPlay
              muted
              loop
              playsInline
              controls={true}
              style={{ objectFit: 'contain' }}
              onError={(e) => {
                logger.warn('Erreur de chargement vidéo:', currentMedia.url);
                e.target.style.display = 'none';
              }}
            >
              Votre navigateur ne supporte pas cette vidéo.
            </video>
          ) : (
            <div className="media-error">
              <p>Type de média non supporté</p>
            </div>
          )}
        </div>

        {/* Navigation desktop */}
        {validMedia.length > 1 && (
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
              disabled={currentMediaIndex === validMedia.length - 1}
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
        {validMedia.length > 1 && (
          <div className="progress-indicator">
            {currentMediaIndex + 1} / {validMedia.length}
          </div>
        )}
      </div>

      {/* Thumbnails - Afficher TOUS les médias sans condition */}
      {controls}

      {validMedia && validMedia.length > 0 && (
        <div className="thumbnails-container">
          <div className="thumbnails">
            {validMedia.map((item, index) => (
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
                    style={{ objectFit: 'cover' }}
                    onError={(e) => {
                      logger.warn('Erreur thumbnail image:', item.url);
                      e.target.style.display = 'none';
                    }}
                  />
                ) : item.type === 'video' ? (
                  <div className="thumbnail-video">
                    <video
                      src={item.url}
                      className="thumbnail-video-player"
                      muted
                      loop
                      playsInline
                      style={{ objectFit: 'cover' }}
                      onError={(e) => {
                        logger.warn('Erreur thumbnail vidéo:', item.url);
                        e.target.style.display = 'none';
                      }}
                    />
                    <div className="thumbnail-video-overlay">
                      <span>▶</span>
                    </div>
                  </div>
                ) : (
                  <div className="thumbnail-error">
                    <span>?</span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      <AnimatePresence>
        {isZoomed && (
          <Motion.div
            className="zoom-overlay"
            onClick={() => setIsZoomed(false)}
            variants={backdropVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={overlayTransition}
          >
            <Motion.div
              className="zoomed-image-container"
              variants={zoomModalVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={zoomTransition}
              onClick={(event) => event.stopPropagation()}
            >
              {currentMedia.type === 'image' && (
                <img
                  src={currentMedia.url}
                  alt={`${productName} - Zoom`}
                  className="zoomed-image"
                />
              )}
            </Motion.div>
            <button className="zoom-close" onClick={() => setIsZoomed(false)}>
              ✕
            </button>
          </Motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ProductGallery;
