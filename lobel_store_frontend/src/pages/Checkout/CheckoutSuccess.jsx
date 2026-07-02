import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { confirmMockPayment } from '../../api/payments';
import { toast } from '../../components/ui/toast';
import {
  clearPendingCheckout,
  getPendingCheckout,
} from '../../utils/pendingCheckout';
import './CheckoutSuccess.css';

const CheckoutSuccess = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [phase, setPhase] = useState('confirming');
  const [orderId, setOrderId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    const confirmPayment = async () => {
      const pending = getPendingCheckout();
      const paymentId =
        searchParams.get('paymentId') ||
        (pending?.paymentId != null ? String(pending.paymentId) : null);
      const resolvedOrderId =
        searchParams.get('orderId') ||
        (pending?.orderId != null ? String(pending.orderId) : null);

      if (!paymentId) {
        setErrorMessage('Identifiant de paiement introuvable.');
        setPhase('error');
        return;
      }

      try {
        const result = await confirmMockPayment(Number(paymentId));
        clearPendingCheckout();
        setOrderId(result.orderId ?? resolvedOrderId);
        toast.success('Paiement confirmé');
        setPhase('success');
      } catch (err) {
        const message =
          err?.response?.data?.detail ||
          err?.message ||
          'Impossible de confirmer le paiement.';
        setErrorMessage(message);
        setPhase('error');
        toast.error(message);
      }
    };

    if (searchParams.get('mock') === 'true') {
      confirmPayment();
      return;
    }

    setErrorMessage('Cette page nécessite un paiement mock.');
    setPhase('error');
  }, [searchParams]);

  return (
    <div className="checkout-success-page">
      <div className="checkout-success-card">
        {phase === 'confirming' && (
          <>
            <h1>Confirmation en cours...</h1>
            <p>Veuillez patienter pendant la validation de votre commande.</p>
          </>
        )}

        {phase === 'success' && (
          <>
            <h1>Paiement confirmé</h1>
            <p>Votre commande a été validée avec succès.</p>
            {orderId && <p className="checkout-success-order">Commande #{orderId}</p>}
            <button
              type="button"
              className="checkout-success-btn"
              onClick={() => navigate('/shop')}
            >
              Continuer mes achats
            </button>
          </>
        )}

        {phase === 'error' && (
          <>
            <h1>Confirmation impossible</h1>
            <p>{errorMessage}</p>
            <button
              type="button"
              className="checkout-success-btn"
              onClick={() => navigate('/checkout')}
            >
              Retour au checkout
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default CheckoutSuccess;
