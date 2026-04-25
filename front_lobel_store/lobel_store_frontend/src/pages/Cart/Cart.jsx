import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCart } from '../../api/cart';
import './Cart.css';

const Cart = () => {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadCart = async () => {
      try {
        setLoading(true);
        setError('');
        const cartData = await fetchCart({ notify: false });
        setCart(cartData);
      } catch (err) {
        console.error('Error fetching cart:', err);
        setError('Impossible de charger le panier.');
      } finally {
        setLoading(false);
      }
    };

    loadCart();
    window.addEventListener('cartUpdated', loadCart);

    return () => {
      window.removeEventListener('cartUpdated', loadCart);
    };
  }, []);

  const items = cart?.items ?? [];

  return (
    <div className="cart-page">
      <div className="cart-container">
        <h1>Mon Panier</h1>
        <div className="cart-content">
          {loading ? (
            <div className="cart-empty">
              <p>Chargement du panier...</p>
            </div>
          ) : error ? (
            <div className="cart-empty">
              <p>{error}</p>
              <button
                className="continue-shopping-btn"
                onClick={() => navigate('/shop')}
              >
                Continuer mes achats
              </button>
            </div>
          ) : items.length === 0 ? (
            <div className="cart-empty">
              <p>Votre panier est vide</p>
              <button
                className="continue-shopping-btn"
                onClick={() => navigate('/shop')}
              >
                Continuer mes achats
              </button>
            </div>
          ) : (
            <div className="cart-items-wrapper">
              <div className="cart-items">
                {items.map((item) => (
                  <div key={item.id} className="cart-item">
                    <div className="cart-item-image">
                      {item.product?.image ? (
                        <img src={item.product.image} alt={item.product?.name || 'Produit'} />
                      ) : (
                        <div className="cart-item-image-placeholder">Image</div>
                      )}
                    </div>

                    <div className="cart-item-details">
                      <h2>{item.product?.name || 'Produit sans nom'}</h2>
                      <p>Quantite : {item.quantity}</p>
                      <p>
                        Prix unitaire : {Number(item.product?.price || 0).toLocaleString()} FCFA
                      </p>
                      <p>
                        Total : {Number((item.product?.price || 0) * item.quantity).toLocaleString()} FCFA
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="cart-summary">
                <p>Articles : {cart?.cart_items ?? items.length}</p>
                <p>Total : {Number(cart?.cart_total || 0).toLocaleString()} FCFA</p>
                <button
                  className="continue-shopping-btn"
                  onClick={() => navigate('/checkout')}
                >
                  Passer au paiement
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Cart;
