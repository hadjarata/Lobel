import React, { useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../../cart/cartState';
import { useAuth } from '../../context/authState';
import './Cart.css';

const money = (value, currency = 'XOF') => {
  if (value == null) return '—';
  return `${String(value)} ${currency}`;
};

const Cart = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const {
    status, cart, lines, itemCount, isGuest, error, lineErrors,
    pendingLines, mergeReport, updateItemQuantity, removeItem, reloadCart,
  } = useCart();
  const announcement = useRef(null);
  const loading = status === 'idle' || status === 'loading';
  const hasInvalidLine = lines.some((line) => line.invalid || lineErrors[line.id] || lineErrors[line.variant_id]);

  const changeQuantity = async (item, delta) => {
    const quantity = item.quantity + delta;
    if (quantity < 1) return;
    try {
      await updateItemQuantity(item, quantity);
      if (announcement.current) announcement.current.textContent = 'Quantité mise à jour.';
    } catch {
      if (announcement.current) announcement.current.textContent = 'La quantité n’a pas été modifiée.';
    }
  };

  const remove = async (item) => {
    const nextFocus = document.querySelector(`[data-cart-line]:not([data-cart-line="${item.id}"]) button`);
    try {
      await removeItem(item);
      if (announcement.current) announcement.current.textContent = 'Article retiré du panier.';
      nextFocus?.focus();
    } catch {
      if (announcement.current) announcement.current.textContent = 'La suppression a échoué.';
    }
  };

  return (
    <main className="cart-page">
      <header className="cart-header">
        <div className="cart-header-text">
          <p className="cart-eyebrow">Votre sélection</p>
          <h1 className="cart-title">Mon panier</h1>
          {!loading && <p className="cart-subtitle">{itemCount} unité{itemCount > 1 ? 's' : ''}</p>}
        </div>
        <Link to="/shop" className="cart-continue-link">Continuer mes achats</Link>
      </header>
      <div ref={announcement} className="sr-only" role="status" aria-live="polite" />
      {mergeReport && (mergeReport.adjusted_items.length > 0 || mergeReport.rejected_items.length > 0) && (
        <div className="cart-merge-report" role="status">
          Le panier a été synchronisé. Certaines quantités ont été ajustées ou conservées
          localement faute de disponibilité.
        </div>
      )}
      {loading ? (
        <div className="cart-loading" aria-live="polite"><div className="cart-spinner" /><p>Chargement du panier…</p></div>
      ) : error ? (
        <div className="shop-error" role="alert"><p>{error.message}</p><button onClick={reloadCart}>Réessayer</button></div>
      ) : lines.length === 0 ? (
        <div className="cart-empty">
          <h2 className="cart-empty-title">Votre panier est vide</h2>
          <Link to="/shop" className="cart-btn cart-btn-primary">Découvrir la boutique</Link>
        </div>
      ) : (
        <div className="cart-layout">
          <section className="cart-items-panel" aria-label="Articles du panier">
            <ul className="cart-item-list">
              {lines.map((item) => {
                const key = item.id;
                const busy = pendingLines.includes(key);
                const itemError = lineErrors[key] || lineErrors[item.variant_id];
                return (
                  <li key={key} className={`cart-item ${item.invalid ? 'invalid' : ''}`} data-cart-line={key}>
                    <div className="cart-item-media">
                      {item.image ? <img src={item.image} alt="" /> : <div className="cart-item-media-placeholder">LOBEL</div>}
                    </div>
                    <div className="cart-item-body">
                      <div className="cart-item-top">
                        <div>
                          <h2 className="cart-item-name">{item.product_name || 'Produit indisponible'}</h2>
                          {item.variant_name && <p>{item.variant_name}</p>}
                          {item.sku && <p>SKU : {item.sku}</p>}
                        </div>
                        <button type="button" className="cart-item-remove" disabled={busy}
                          aria-label={`Retirer ${item.product_name || 'cet article'}`}
                          onClick={() => remove(item)}>×</button>
                      </div>
                      <p className="cart-item-unit-price">Prix unitaire : {money(item.unit_price, item.currency)}</p>
                      <div className="cart-item-actions">
                        <div className="cart-qty-control" aria-label={`Quantité de ${item.product_name || 'l’article'}`}>
                          <button type="button" className="cart-qty-btn" disabled={busy || item.quantity <= 1 || item.invalid}
                            aria-label="Diminuer la quantité" onClick={() => changeQuantity(item, -1)}>−</button>
                          <span className="cart-qty-value" aria-live="polite">{item.quantity}</span>
                          <button type="button" className="cart-qty-btn" disabled={busy || item.invalid}
                            aria-label="Augmenter la quantité" onClick={() => changeQuantity(item, 1)}>+</button>
                        </div>
                        <p className="cart-item-line-total">
                          {isGuest ? 'Confirmé après connexion' : money(item.line_total, item.currency)}
                        </p>
                      </div>
                      {itemError && <p id={`cart-error-${key}`} className="cart-line-error" role="alert">{itemError.message}</p>}
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
                <div className="cart-summary-row"><dt>Unités</dt><dd>{itemCount}</dd></div>
                <div className="cart-summary-row"><dt>Total</dt>
                  <dd>{isGuest ? 'Confirmé après connexion' : money(cart.cart_total, cart.currency)}</dd>
                </div>
              </dl>
              <button type="button" className="cart-btn cart-btn-primary cart-btn-full"
                disabled={hasInvalidLine || lines.length === 0}
                onClick={() => navigate(isAuthenticated ? '/checkout' : '/login', {
                  state: !isAuthenticated ? {
                    from: { pathname: '/checkout' },
                    message: 'Connectez-vous pour synchroniser et finaliser votre panier.',
                  } : undefined,
                })}>
                {isAuthenticated ? 'Continuer vers le checkout' : 'Se connecter pour continuer'}
              </button>
              {hasInvalidLine && <p>Corrigez ou retirez les lignes indisponibles avant de continuer.</p>}
            </div>
          </aside>
        </div>
      )}
    </main>
  );
};

export default Cart;
