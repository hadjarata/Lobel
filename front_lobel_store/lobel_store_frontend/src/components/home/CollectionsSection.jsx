import React, { useState, useEffect } from 'react';
import CollectionCard from '../products/CollectionCard';
import { getCollections, getProducts } from '../../api/products';
import './CollectionsSection.css';

const CollectionsSection = () => {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCollectionsWithProducts = async () => {
      try {
        setLoading(true);
        setError(null);
        const collectionsData = await getCollections();
        const collectionsArray = collectionsData.results || collectionsData;
        
        // Récupérer les produits pour chaque collection
        const collectionsWithProducts = await Promise.all(
          collectionsArray.map(async (collection) => {
            try {
              const productsData = await getProducts();
              const allProducts = productsData.data || productsData;
              
              // Filtrer les produits de cette collection
              const collectionProducts = allProducts.filter(product => 
                product.category?.id === collection.id || 
                product.category === collection.id ||
                product.category?.name?.toLowerCase() === collection.name?.toLowerCase()
              ).slice(0, 6); // Limiter à 6 produits pour l'aperçu
              
              return {
                ...collection,
                products: collectionProducts
              };
            } catch (err) {
              console.error(`Error fetching products for collection ${collection.id}:`, err);
              return {
                ...collection,
                products: []
              };
            }
          })
        );
        
        setCollections(collectionsWithProducts);
      } catch (err) {
        setError('Impossible de charger les collections');
        console.error('Error fetching collections:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCollectionsWithProducts();
  }, []);

  return (
    <section className="collections-section">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">Nos Collections</h2>
          <p className="section-subtitle">
            Explorez nos sélections spéciales pour chaque occasion
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
                image={collection.image}
                products={collection.products || []}
                link={`/shop?category=${collection.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default CollectionsSection;
