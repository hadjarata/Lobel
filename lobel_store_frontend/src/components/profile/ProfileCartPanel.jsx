import React from 'react';
import { Link } from 'react-router-dom';
import { formatPrice } from '../../utils/profileUtils';
import { getProductImageUrl } from '../../utils/mediaUtils';

const ProfileCartPanel = ({ cart, loading, onRefresh }) => {
  if (loading) {
    return (
      <section className="profile-panel">
        <div className="profile-loading-inline">
          <div className="profile-spinner" />
          <p>Chargement du panier...</p>
        </div>
      </section>
    );
  }

  const items = cart?.items ?? [];
  const itemCount = cart?.cart_items ?? 0;
  const cartTotal = cart?.cart_total ?? null;

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Mon panier actif</h2>
          <p className="profile-panel-subtitle">
            Reprenez vos achats ou finalisez votre commande.
          </p>
        </div>
        <button type="button" className="profile-btn profile-btn-ghost" onClick={onRefresh}>
          Actualiser
        </button>
      </div>

      {items.length === 0 ? (
        <div className="profile-empty-state">
          <p>Votre panier est vide.</p>
          <Link to="/shop" className="profile-btn profile-btn-primary">
            Découvrir la boutique
          </Link>
        </div>
      ) : (
        <>
          <div className="profile-stats-row">
            <div className="profile-stat-card">
              <span className="profile-stat-value">{itemCount}</span>
              <span className="profile-stat-label">Articles</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{formatPrice(cartTotal)}</span>
              <span className="profile-stat-label">Total FCFA</span>
            </div>
          </div>

          <ul className="profile-cart-list">
            {items.map((item) => {
              const imageUrl = getProductImageUrl(item.product);
              const lineTotal = item.line_total;

              return (
                <li key={item.id} className="profile-cart-item">
                  <div className="profile-cart-item-media">
                    {imageUrl ? (
                      <img src={imageUrl} alt={item.product?.name || 'Produit'} />
                    ) : (
                      <span>LOBEL</span>
                    )}
                  </div>
                  <div className="profile-cart-item-info">
                    <p>{item.product_name || item.product?.name || 'Produit'}</p>
                    <span>Quantité : {item.quantity}</span>
                  </div>
                  <strong>{formatPrice(lineTotal)} FCFA</strong>
                </li>
              );
            })}
          </ul>

          <div className="profile-cart-actions">
            <Link to="/cart" className="profile-btn profile-btn-outline">
              Voir le panier complet
            </Link>
            <Link to="/checkout" className="profile-btn profile-btn-primary">
              Passer au paiement
            </Link>
          </div>
        </>
      )}
    </section>
  );
};

export default ProfileCartPanel;
