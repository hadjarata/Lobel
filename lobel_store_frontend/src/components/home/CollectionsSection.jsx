import React, { useState, useEffect } from 'react';
import CollectionCard from '../product/CollectionCard';
import { getCollections } from '../../api/products';
import { logger } from '../../utils/logger';
import './CollectionsSection.css';

const CollectionsSection = () => {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCollections = async () => {
      try {
        setLoading(true);
        setError(null);
        const collectionsData = await getCollections();
        setCollections(collectionsData.results);
      } catch (err) {
        setError('Impossible de charger les collections');
        logger.error('Error fetching collections:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, []);

  return (
    <section className="collections-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Nos Collections</h2>
          <p className="section-subtitle">
            Des univers curatés pour exprimer votre style avec grâce
          </p>
        </div>
        {loading ? (
          <div className="collections-loading">
            <div className="loading-spinner"></div>
            <p>Chargement des collections...</p>
          </div>
        ) : error ? (
          <div className="collections-error">
            <p>{error}</p>
            <button className="retry-btn" onClick={() => window.location.reload()}>
              Réessayer
            </button>
          </div>
        ) : collections.length === 0 ? (
          <div className="collections-empty">
            <p>Aucune collection disponible pour le moment.</p>
          </div>
        ) : (
          <div className="collections-grid">
            {collections.map((collection) => (
              <CollectionCard
                key={collection.id}
                title={collection.name || collection.title}
                subtitle={collection.description || collection.subtitle}
                image={collection.image_url || collection.image}
                video={collection.video_url || collection.video}
                coverType={collection.cover_type || 'image'}
                hasProducts={Array.isArray(collection.products) && collection.products.length > 0}
                link={`/shop?collection=${collection.slug}`}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default CollectionsSection;
