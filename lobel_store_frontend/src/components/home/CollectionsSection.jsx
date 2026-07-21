import React, { useState, useEffect } from 'react';
import CollectionCard from '../product/CollectionCard';
import { Button, Card, Section } from '../ui';
import { getCollections } from '../../api/products';
import { logger } from '../../utils/logger';
import HomeReveal, { HomeRevealItem } from './HomeReveal';
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
    <Section
      className="collections-section"
      background="subtle"
      title="Nos Collections"
      subtitle="Des univers curatés pour exprimer votre style avec grâce"
    >
        {loading ? (
          <div className="home-state collections-loading" role="status">
            <span className="home-spinner" aria-hidden="true" />
            <p>Chargement des collections...</p>
          </div>
        ) : error ? (
          <Card className="home-state collections-error">
            <p>{error}</p>
            <Button onClick={() => window.location.reload()}>
              Réessayer
            </Button>
          </Card>
        ) : collections.length === 0 ? (
          <Card className="home-state collections-empty">
            <p>Aucune collection disponible pour le moment.</p>
          </Card>
        ) : (
          <HomeReveal className="collections-grid" stagger>
            {collections.map((collection, index) => (
              <HomeRevealItem
                key={collection.id}
                className="collection-reveal-item"
                data-collection-number={String(index + 1).padStart(2, '0')}
              >
                <CollectionCard
                  title={collection.name || collection.title}
                  subtitle={collection.description || collection.subtitle}
                  image={collection.image_url || collection.image}
                  video={collection.video_url || collection.video}
                  coverType={collection.cover_type || 'image'}
                  hasProducts={Array.isArray(collection.products) && collection.products.length > 0}
                  link={`/shop?collection=${collection.slug}`}
                />
              </HomeRevealItem>
            ))}
          </HomeReveal>
        )}
    </Section>
  );
};

export default CollectionsSection;
