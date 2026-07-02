import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCart } from '../../api/cart';
import { initiateCheckout } from '../../api/payments';
import { toast } from '../../components/ui/toast';
import { savePendingCheckout } from '../../utils/pendingCheckout';
import './Checkout.css';

const Checkout = () => {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [paymentError, setPaymentError] = useState('');
  const [isPaying, setIsPaying] = useState(false);

  const loadCart = async () => {
    try {
      setLoading(true);
      setError('');
      const cartData = await fetchCart({ notify: false });
      setCart(cartData);
      return cartData;
    } catch (err) {
      console.error('Error fetching cart:', err);
      setError('Impossible de charger le panier.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, []);

  const items = cart?.items ?? [];
  const hasItems = items.length > 0;

  const handlePay = async () => {
    const latestCart = await loadCart();

    if (!latestCart?.items?.length || isPaying) {
      toast.warning('Votre panier est vide.');
      return;
    }

    setPaymentError('');
    setIsPaying(true);

    try {
      const data = await initiateCheckout();

      if (data?.paymentId != null) {
        savePendingCheckout({
          paymentId: data.paymentId,
          orderId: data.orderId ?? null,
          sessionToken: data.sessionToken ?? null,
        });
      }

      if (!data?.payment_url) {
        setPaymentError('Réponse de paiement invalide. Veuillez réessayer.');
        setIsPaying(false);
        return;
      }

      toast.info('Redirection vers la confirmation de paiement...');
      window.location.href = data.payment_url;
    } catch (err) {
      const message =
        err?.response?.data?.detail ||
        err?.message ||
        'Impossible de démarrer le paiement.';
      setPaymentError(message);
      toast.error(message);
      setIsPaying(false);
    }
  };

  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <h1>Finaliser la commande</h1>

        <div className="checkout-content">
          {loading ? (
            <div className="checkout-empty">
              <p>Chargement du panier...</p>
            </div>
          ) : error ? (
            <div className="checkout-empty">
              <p>{error}</p>
              <button
                type="button"
                className="continue-shopping-btn"
                onClick={() => navigate('/shop')}
              >
                Retour à la boutique
              </button>
            </div>
          ) : !hasItems ? (
            <div className="checkout-empty">
              <p>Votre panier est vide.</p>
              <button
                type="button"
                className="continue-shopping-btn"
                onClick={() => navigate('/shop')}
              >
                Continuer mes achats
              </button>
            </div>
          ) : (
            <>
              <ul className="checkout-item-list">
                {items.map((item) => {
                  const unitPrice = Number(item.product?.price || 0);
                  const lineTotal = unitPrice * item.quantity;

                  return (
                    <li key={item.id} className="checkout-item">
                      <div>
                        <h3>{item.product?.name || 'Produit'}</h3>
                        <p>Quantité : {item.quantity}</p>
                        <p>Prix unitaire : {unitPrice.toLocaleString('fr-FR')} FCFA</p>
                      </div>
                      <strong>{lineTotal.toLocaleString('fr-FR')} FCFA</strong>
                    </li>
                  );
                })}
              </ul>

              <div className="checkout-summary">
                <p>Articles : {cart?.cart_items ?? items.length}</p>
                <p>Total : {Number(cart?.cart_total || 0).toLocaleString('fr-FR')} FCFA</p>

                {paymentError && (
                  <p className="checkout-error-message" role="alert">
                    {paymentError}
                  </p>
                )}

                <button
                  type="button"
                  className="checkout-pay-btn"
                  onClick={handlePay}
                  disabled={isPaying}
                >
                  {isPaying ? 'Préparation du paiement...' : 'Payer (mode test)'}
                </button>

                <button
                  type="button"
                  className="continue-shopping-btn"
                  onClick={() => navigate('/cart')}
                  disabled={isPaying}
                >
                  Retour au panier
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Checkout;
