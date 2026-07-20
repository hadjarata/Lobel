import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../../cart/cartState';
import {
  createCheckoutOrder,
  getDeliveryOptions,
  getPendingCheckoutOrder,
  previewCheckout,
} from '../../api/checkout';
import { formatPrice } from '../../utils/profileUtils';
import { initializePayment, recordPaymentRedirect } from '../../api/payments';
import { savePendingCheckout } from '../../utils/pendingCheckout';
import { canRedirectPayment } from '../../payments/paymentPolicy';
import './Checkout.css';

const EMPTY_ADDRESS = {
  recipient_name: '', phone: '', country: 'ML', region: '',
  city: '', district: '', street: '', instructions: '',
};

const newIdempotencyKey = () => (
  globalThis.crypto?.randomUUID?.()
  || `checkout-${Date.now()}-${Math.random().toString(16).slice(2)}`
);

const Checkout = () => {
  const navigate = useNavigate();
  const { lines, isGuest, status: cartStatus, reloadCart } = useCart();
  const [step, setStep] = useState(1);
  const [address, setAddress] = useState(EMPTY_ADDRESS);
  const [methods, setMethods] = useState([]);
  const [deliveryMethod, setDeliveryMethod] = useState('');
  const [preview, setPreview] = useState(null);
  const [pendingOrder, setPendingOrder] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(newIdempotencyKey);
  const [paymentKey] = useState(newIdempotencyKey);

  useEffect(() => {
    if (!isGuest) {
      getPendingCheckoutOrder()
        .then(({ order }) => {
          if (order) {
            setPendingOrder(order);
            setStep(4);
          }
        })
        .catch(() => {});
    }
  }, [isGuest]);

  const validAddress = useMemo(() => (
    address.recipient_name.trim().length >= 2
    && /^\+?[0-9][0-9 .-]{7,19}$/.test(address.phone)
    && address.city.trim().length >= 2
    && address.street.trim().length >= 3
  ), [address]);

  const payload = (version) => ({
    shipping_address: address,
    delivery_method: deliveryMethod,
    billing_same_as_shipping: true,
    ...(version ? { checkout_version: version } : {}),
  });

  const submitAddress = async (event) => {
    event.preventDefault();
    if (!validAddress) {
      setError('Complétez correctement les champs obligatoires.');
      return;
    }
    setBusy(true); setError('');
    try {
      const result = await getDeliveryOptions(address);
      setMethods(result.delivery_methods || []);
      setDeliveryMethod(result.delivery_methods?.[0]?.code || '');
      setStep(2);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const submitDelivery = async () => {
    if (!deliveryMethod) return;
    setBusy(true); setError('');
    try {
      const result = await previewCheckout(payload());
      setPreview(result);
      setStep(3);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const createOrder = async () => {
    if (!preview || busy) return;
    setBusy(true); setError('');
    try {
      const result = await createCheckoutOrder(
        payload(preview.checkout_version), idempotencyKey,
      );
      setPendingOrder(result.order);
      setStep(4);
      await reloadCart();
    } catch (requestError) {
      setError(requestError.message);
      if (requestError.code === 'stale_checkout') {
        setPreview(null);
        setStep(2);
        setIdempotencyKey(newIdempotencyKey());
      }
      if (requestError.code === 'order_already_created') {
        const result = await getPendingCheckoutOrder().catch(() => ({ order: null }));
        if (result.order) {
          setPendingOrder(result.order);
          setStep(4);
        }
      }
    } finally {
      setBusy(false);
    }
  };

  const proceedToPayment = async () => {
    if (!pendingOrder || busy) return;
    setBusy(true); setError('');
    try {
      const session = await initializePayment({
        orderId: pendingOrder.id,
        idempotencyKey: paymentKey,
      });
      if (!canRedirectPayment(session, pendingOrder.id)) {
        throw new Error('Session de paiement incohérente.');
      }
      savePendingCheckout({
        paymentId: session.payment_id,
        orderId: session.order_id,
      });
      await recordPaymentRedirect(session.payment_id);
      window.location.assign(session.checkout_url);
    } catch (requestError) {
      setError(requestError.message || 'Impossible d’initialiser le paiement.');
      setBusy(false);
    }
  };

  if (isGuest) {
    return (
      <main className="checkout-page">
        <div className="checkout-content checkout-empty">
          <h1>Connexion requise</h1>
          <p>Connectez-vous pour utiliser votre panier serveur et finaliser la commande.</p>
          <button type="button" className="checkout-pay-btn" onClick={() => navigate('/login')}>
            Se connecter
          </button>
        </div>
      </main>
    );
  }

  if (cartStatus === 'loading' && !pendingOrder) {
    return <main className="checkout-page"><p>Chargement du checkout…</p></main>;
  }

  if (!lines.length && !pendingOrder) {
    return (
      <main className="checkout-page">
        <div className="checkout-content checkout-empty">
          <h1>Votre panier est vide</h1>
          <button type="button" className="continue-shopping-btn" onClick={() => navigate('/shop')}>
            Continuer mes achats
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="checkout-page">
      <div className="checkout-container">
        <h1>Finaliser la commande</h1>
        <ol className="checkout-steps" aria-label="Étapes du checkout">
          {['Adresse', 'Livraison', 'Récapitulatif', 'Prête à payer'].map((label, index) => (
            <li key={label} aria-current={step === index + 1 ? 'step' : undefined}
              className={step >= index + 1 ? 'active' : ''}>{label}</li>
          ))}
        </ol>
        <div className="checkout-content">
          {error && <p className="checkout-error-message" role="alert">{error}</p>}

          {step === 1 && (
            <form className="checkout-form" onSubmit={submitAddress}>
              <label>Nom du destinataire*
                <input value={address.recipient_name} autoComplete="name"
                  onChange={(e) => setAddress({ ...address, recipient_name: e.target.value })} />
              </label>
              <label>Téléphone*
                <input value={address.phone} autoComplete="tel"
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })} />
              </label>
              <label>Ville*
                <input value={address.city} autoComplete="address-level2"
                  onChange={(e) => setAddress({ ...address, city: e.target.value })} />
              </label>
              <label>Quartier
                <input value={address.district}
                  onChange={(e) => setAddress({ ...address, district: e.target.value })} />
              </label>
              <label>Rue et repère*
                <input value={address.street} autoComplete="street-address"
                  onChange={(e) => setAddress({ ...address, street: e.target.value })} />
              </label>
              <label>Instructions de livraison
                <textarea value={address.instructions}
                  onChange={(e) => setAddress({ ...address, instructions: e.target.value })} />
              </label>
              <button className="checkout-pay-btn" disabled={busy || !validAddress}>
                {busy ? 'Vérification…' : 'Choisir la livraison'}
              </button>
            </form>
          )}

          {step === 2 && (
            <section>
              <h2>Mode de livraison</h2>
              {methods.map((method) => (
                <label className="delivery-option" key={method.code}>
                  <input type="radio" name="delivery" value={method.code}
                    checked={deliveryMethod === method.code}
                    onChange={() => setDeliveryMethod(method.code)} />
                  <span><strong>{method.label}</strong><br />
                    {formatPrice(method.fee)} FCFA · {method.eta_min_days}–{method.eta_max_days} jour(s)
                  </span>
                </label>
              ))}
              <button type="button" className="checkout-pay-btn"
                disabled={busy || !deliveryMethod} onClick={submitDelivery}>
                {busy ? 'Calcul…' : 'Voir le récapitulatif'}
              </button>
              <button type="button" className="checkout-link-btn" onClick={() => setStep(1)}>
                Modifier l’adresse
              </button>
            </section>
          )}

          {step === 3 && preview && (
            <section>
              <h2>Récapitulatif calculé par LobelStore</h2>
              <ul className="checkout-item-list">
                {preview.lines.map((line) => (
                  <li className="checkout-item" key={line.line_id}>
                    <span>{line.product_name} · {line.variant_name} × {line.quantity}</span>
                    <strong>{formatPrice(line.line_total)} FCFA</strong>
                  </li>
                ))}
              </ul>
              <div className="checkout-totals">
                <p>Sous-total <strong>{formatPrice(preview.amounts.subtotal)} FCFA</strong></p>
                <p>Livraison <strong>{formatPrice(preview.amounts.shipping)} FCFA</strong></p>
                <p>Total <strong>{formatPrice(preview.amounts.total)} FCFA</strong></p>
              </div>
              {preview.warnings?.map((warning) => (
                <p className="checkout-warning" key={`${warning.code}-${warning.line_id}`}>
                  Le prix d’un article a été actualisé.
                </p>
              ))}
              <button type="button" className="checkout-pay-btn" disabled={busy} onClick={createOrder}>
                {busy ? 'Création sécurisée…' : 'Créer la commande'}
              </button>
              <p className="checkout-help">Aucun paiement ne sera déclenché à cette étape.</p>
              <button type="button" className="checkout-link-btn" onClick={() => setStep(2)}>
                Modifier la livraison
              </button>
            </section>
          )}

          {step === 4 && pendingOrder && (
            <section className="checkout-ready">
              <h2>Commande #{pendingOrder.id} prête à payer</h2>
              <p>La commande est figée et enregistrée. Son paiement n’a pas encore été initialisé.</p>
              <p className="checkout-ready-total">
                Total : {formatPrice(pendingOrder.total_amount)} {pendingOrder.currency}
              </p>
              <button type="button" className="checkout-pay-btn"
                disabled={busy || pendingOrder.status !== 'pending_payment'}
                onClick={proceedToPayment}>
                {busy ? 'Initialisation du paiement…' : 'Procéder au paiement'}
              </button>
              <p className="checkout-help">Vous serez redirigé vers la page sécurisée LigdiCash.</p>
              <button type="button" className="continue-shopping-btn" onClick={() => navigate('/profile')}>
                Voir mes commandes
              </button>
            </section>
          )}
        </div>
      </div>
    </main>
  );
};

export default Checkout;
