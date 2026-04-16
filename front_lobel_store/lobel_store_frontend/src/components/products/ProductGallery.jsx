import React, { useState } from 'react';
import './ProductGallery.css';

const ProductGallery = ({ images = [] }) => {
  const [mainImageIndex, setMainImageIndex] = useState(0);

  const handleThumbnailClick = (index) => {
    setMainImageIndex(index);
  };

  const handlePrevImage = () => {
    setMainImageIndex((prev) => 
      prev === 0 ? images.length - 1 : prev - 1
    );
  };

  const handleNextImage = () => {
    setMainImageIndex((prev) => 
      prev === images.length - 1 ? 0 : prev + 1
    );
  };

  if (!images || images.length === 0) {
    return (
      <div className="product-gallery">
        <div className="gallery-placeholder">
          <div className="placeholder-image">
            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#FFB6C1" strokeWidth="1">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21,15 16,10 5,21"></polyline>
            </svg>
          </div>
        </div>
      </div>
    );
  }

  const mainImage = images[mainImageIndex];

  return (
    <div className="product-gallery">
      <div className="main-image-container">
        <img 
          src={mainImage} 
          alt="Product main image"
          className="main-image"
        />
        
        {images.length > 1 && (
          <>
            <button 
              className="gallery-nav gallery-nav-prev"
              onClick={handlePrevImage}
              aria-label="Image précédente"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="15,18 9,12 15,6"></polyline>
              </svg>
            </button>
            
            <button 
              className="gallery-nav gallery-nav-next"
              onClick={handleNextImage}
              aria-label="Image suivante"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9,18 15,12 9,6"></polyline>
              </svg>
            </button>
          </>
        )}
      </div>

      {images.length > 1 && (
        <div className="thumbnails-container">
          <div className="thumbnails-grid">
            {images.map((image, index) => (
              <button
                key={index}
                className={`thumbnail ${index === mainImageIndex ? 'active' : ''}`}
                onClick={() => handleThumbnailClick(index)}
                aria-label={`Voir image ${index + 1}`}
              >
                <img 
                  src={image} 
                  alt={`Product thumbnail ${index + 1}`}
                  className="thumbnail-image"
                />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductGallery;
