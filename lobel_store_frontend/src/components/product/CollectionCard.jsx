import React from 'react';
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
  coverType = 'image',
  hasProducts = false,
  link = '/shop',
}) => {
  const coverVideo = coverType === 'video' ? normalizeMediaUrl(video) : null;
  const coverImage = normalizeMediaUrl(image);

  const renderCover = () => {
    if (coverVideo) {
      return (
        <video
          src={coverVideo}
          className="collection-cover-media"
          autoPlay
          muted
          loop
          playsInline
        />
      );
    }

    if (coverImage) {
      return (
        <img
          src={coverImage}
          alt={title}
          className="collection-cover-media"
          loading="lazy"
        />
      );
    }

    return (
      <div className="collection-empty-background" aria-hidden="true">
        <div className="collection-empty-pattern"></div>
      </div>
    );
  };

  return (
    <article className="collection-card">
      <div className="collection-cover-container">{renderCover()}</div>

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
            {hasProducts ? 'Voir la collection' : 'Découvrir la collection'}
          </Link>
        </div>
      </div>
    </article>
  );
};

export default CollectionCard;
