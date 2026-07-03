import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  fetchCart,
  removeCartItem,
  updateCartItemQuantity,
} from '../../api/cart';
import { useAuth } from '../../context/AuthContext';
import { toast } from '../../components/ui/toast';
import { getProductImageUrl } from '../../utils/mediaUtils';
import './Cart.css';

const formatPrice = (value) =>
  Number(value || 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 });

const Cart = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyItemId, setBusyItemId] = useState(null);

  const loadCart = useCallback(async ({ notify = false } = {}) => {
    try {
      setError('');
      const cartData = await fetchCart({ notify });
      setCart(cartData);
      return cartData;
    } catch (err) {
      console.error('Error fetching cart:', err);
      setError('Impossible de charger le panier.');
      return null;
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await loadCart({ notify: false });
      setLoading(false);
    };

    init();

    const handleCartUpdated = () => {
      loadCart({ notify: false });
    };

    window.addEventListener('cartUpdated', handleCartUpdated);
    return () => window.removeEventListener('cartUpdated', handleCartUpdated);
  }, [loadCart]);

  const items = cart?.items ?? [];
  const itemCount = cart?.cart_items ?? items.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cart?.cart_total ?? 0;

  const handleQuantityChange = async (item, delta) => {
    const nextQuantity = item.quantity + delta;

    if (nextQuantity < 1) {
      await handleRemoveItem(item);
      return;
    }

    setBusyItemId(item.id);

    try {
      await updateCartItemQuantity(item, nextQuantity);
      await loadCart({ notify: true });
    } catch (err) {
      console.error('Error updating quantity:', err);
      toast.error('Impossible de mettre à jour la quantité.');
    } finally {
      setBusyItemId(null);
    }
  };

  const handleRemoveItem = async (item) => {
    setBusyItemId(item.id);

    try {
      await removeCartItem(item);
      await loadCart({ notify: true });
      toast.success('Article retiré du panier');
    } catch (err) {
      console.error('Error removing item:', err);
      toast.error('Impossible de retirer cet article.');
    } finally {
      setBusyItemId(null);
    }
  };

  const handleCheckout = () => {
    if (!isAuthenticated) {
      navigate('/login', {
        state: {
          from: { pathname: '/checkout' },
          message: 'Connectez-vous pour finaliser votre commande. Votre panier sera conservé.',
        },
      });
      return;
    }

    navigate('/checkout');
  };

  const renderEmptyState = (message, showCta = true) => (
    <div className="cart-empty">
      <div className="cart-empty-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2">
          <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4H6z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 0 1-8 0" />
        </svg>
      </div>
      <h2 className="cart-empty-title">{message}</h2>
      <p className="cart-empty-text">
        Parcourez nos collections et trouvez la pièce qui vous correspond.
      </p>
      {showCta && (
        <Link to="/shop" className="cart-btn cart-btn-primary">
          Découvrir la boutique
        </Link>
      )}
    </div>
  );

  return (
    <div className="cart-page">
      <header className="cart-header">
        <div className="cart-header-text">
          <p className="cart-eyebrow">Votre sélection</p>
          <h1 className="cart-title">Mon Panier</h1>
          {!loading && !error && items.length > 0 && (
            <p className="cart-subtitle">
              {itemCount} article{itemCount > 1 ? 's' : ''} · Total {formatPrice(cartTotal)} FCFA
            </p>
          )}
        </div>
        {!loading && items.length > 0 && (
          <Link to="/shop" className="cart-continue-link">
            Continuer mes achats
          </Link>
        )}
      </header>

      {loading ? (
        <div className="cart-loading">
          <div className="cart-spinner" />
          <p>Chargement de votre panier...</p>
        </div>
      ) : error ? (
        renderEmptyState(error, false)
      ) : items.length === 0 ? (
        renderEmptyState('Votre panier est vide')
      ) : (
        <div className="cart-layout">
          <section className="cart-items-panel" aria-label="Articles du panier">
            <ul className="cart-item-list">
              {items.map((item) => {
                const unitPrice = Number(item.product?.price || 0);
                const lineTotal = unitPrice * item.quantity;
                const isBusy = busyItemId === item.id;
                const productId = item.product?.id;
                const productName = item.product?.name || 'Produit';
                const productImage = getProductImageUrl(item.product);

                return (
                  <li key={item.id} className="cart-item">
                    {productId ? (
                      <Link to={`/product/${productId}`} className="cart-item-media">
                        {productImage ? (
                          <img src={productImage} alt={productName} />
                        ) : (
                          <div className="cart-item-media-placeholder">LOBEL</div>
                        )}
                      </Link>
                    ) : (
                      <div className="cart-item-media">
                        {productImage ? (
                          <img src={productImage} alt={productName} />
                        ) : (
                          <div className="cart-item-media-placeholder">LOBEL</div>
                        )}
                      </div>
                    )}

                    <div className="cart-item-body">
                      <div className="cart-item-top">
                        {productId ? (
                          <Link to={`/product/${productId}`} className="cart-item-name">
                            {productName}
                          </Link>
                        ) : (
                          <h2 className="cart-item-name">{productName}</h2>
                        )}
                        <button
                          type="button"
                          className="cart-item-remove"
                          onClick={() => handleRemoveItem(item)}
                          disabled={isBusy}
                          aria-label={`Retirer ${productName} du panier`}
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                            <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                            <line x1="10" y1="11" x2="10" y2="17" />
                            <line x1="14" y1="11" x2="14" y2="17" />
                          </svg>
                        </button>
                      </div>

                      <p className="cart-item-unit-price">
                        {formatPrice(unitPrice)} FCFA / unité
                      </p>

                      <div className="cart-item-actions">
                        <div className="cart-qty-control">
                          <button
                            type="button"
                            className="cart-qty-btn"
                            onClick={() => handleQuantityChange(item, -1)}
                            disabled={isBusy}
                            aria-label="Diminuer la quantité"
                          >
                            −
                          </button>
                          <span className="cart-qty-value">{item.quantity}</span>
                          <button
                            type="button"
                            className="cart-qty-btn"
                            onClick={() => handleQuantityChange(item, 1)}
                            disabled={isBusy}
                            aria-label="Augmenter la quantité"
                          >
                            +
                          </button>
                        </div>

                        <p className="cart-item-line-total">
                          {formatPrice(lineTotal)} <span>FCFA</span>
                        </p>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <aside className="cart-summary-panel" aria-label="Récapitulatif">
            <div className="cart-summary-card">
              <h2 className="cart-summary-title">Récapitulatif</h2>

              <dl className="cart-summary-rows">
                <div className="cart-summary-row">
                  <dt>Sous-total</dt>
                  <dd>{formatPrice(cartTotal)} FCFA</dd>
                </div>
                <div className="cart-summary-row">
                  <dt>Articles</dt>
                  <dd>{itemCount}</dd>
                </div>
                <div className="cart-summary-row cart-summary-row-muted">
                  <dt>Livraison</dt>
                  <dd>Calculée à l&apos;étape suivante</dd>
                </div>
              </dl>

              <div className="cart-summary-total">
                <span>Total</span>
                <strong>{formatPrice(cartTotal)} FCFA</strong>
              </div>

              <button
                type="button"
                className="cart-btn cart-btn-primary cart-btn-full"
                onClick={handleCheckout}
              >
                Passer au paiement
              </button>

              {!isAuthenticated && items.length > 0 && (
                <p className="cart-guest-note">
                  Connexion requise uniquement pour finaliser la commande.
                </p>
              )}

              <Link to="/shop" className="cart-btn cart-btn-ghost cart-btn-full">
                Continuer mes achats
              </Link>

              <p className="cart-summary-note">
                Paiement sécurisé · Confirmation par e-mail
              </p>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
};

export default Cart;
