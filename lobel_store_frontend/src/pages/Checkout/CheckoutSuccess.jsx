import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  confirmMockPayment, getPaymentById, refreshPaymentStatus,
} from '../../api/payments';
import { clearPendingCheckout, getPendingCheckout } from '../../utils/pendingCheckout';
import { publicConfig } from '../../config/env';
import { paymentPollDelay } from '../../payments/paymentPolicy';
import './CheckoutSuccess.css';

const FINAL = new Set(['completed', 'failed', 'cancelled', 'expired']);
const MAX_ATTEMPTS = 8;

const CheckoutSuccess = () => {
  const navigate = useNavigate();
  const [initialPending] = useState(getPendingCheckout);
  const [payment, setPayment] = useState(null);
  const [phase, setPhase] = useState(
    initialPending?.paymentId ? 'verifying' : 'unknown',
  );
  const [message, setMessage] = useState(
    initialPending?.paymentId
      ? 'Vérification sécurisée du paiement…'
      : 'Aucun paiement en attente n’a été retrouvé.',
  );
  const stopped = useRef(false);

  useEffect(() => {
    window.history.replaceState({}, document.title, '/checkout/payment/return');
    const pending = initialPending;
    if (!pending?.paymentId) {
      return undefined;
    }
    stopped.current = false;
    let timer;
    const verify = async (attempt = 0) => {
      if (stopped.current || document.visibilityState === 'hidden') return;
      try {
        if (publicConfig.paymentMockEnabled && attempt === 0) {
          await confirmMockPayment(pending.paymentId).catch(() => null);
        }
        const current = attempt === 0
          ? await getPaymentById(pending.paymentId)
          : await refreshPaymentStatus(pending.paymentId);
        if (stopped.current) return;
        setPayment(current);
        if (current.status === 'completed' && current.order?.status === 'paid') {
          setPhase('success'); setMessage('Paiement confirmé par le serveur.');
          clearPendingCheckout(); return;
        }
        if (FINAL.has(current.status)) {
          setPhase(current.status); setMessage('Le paiement n’a pas été confirmé.'); return;
        }
        if (attempt >= MAX_ATTEMPTS - 1) {
          setPhase('pending'); setMessage('La confirmation prend plus de temps que prévu.'); return;
        }
        timer = window.setTimeout(() => verify(attempt + 1), paymentPollDelay(attempt));
      } catch {
        if (!stopped.current) {
          setPhase('network'); setMessage('Impossible de vérifier le paiement pour le moment.');
        }
      }
    };
    verify();
    return () => {
      stopped.current = true;
      window.clearTimeout(timer);
    };
  }, [initialPending]);

  const retry = async () => {
    const pending = getPendingCheckout();
    if (!pending?.paymentId) return;
    setPhase('verifying');
    try {
      const current = await refreshPaymentStatus(pending.paymentId);
      setPayment(current);
      if (current.status === 'completed' && current.order?.status === 'paid') {
        setPhase('success'); setMessage('Paiement confirmé par le serveur.');
        clearPendingCheckout();
      } else {
        setPhase(current.status); setMessage('Statut relu depuis le serveur.');
      }
    } catch {
      setPhase('network'); setMessage('Vérification temporairement indisponible.');
    }
  };

  return (
    <main className="checkout-success-page">
      <section className="checkout-success-card" aria-live="polite">
        <h1>{phase === 'success' ? 'Paiement confirmé' : 'Suivi du paiement'}</h1>
        <p>{message}</p>
        {payment?.order?.id && <p>Commande #{payment.order.id}</p>}
        {payment?.amount && <p>{payment.amount} {payment.currency}</p>}
        {phase !== 'success' && (
          <button type="button" className="checkout-success-btn" onClick={retry}>
            Vérifier à nouveau
          </button>
        )}
        <button type="button" className="checkout-success-btn" onClick={() => navigate('/profile')}>
          Voir ma commande
        </button>
        {payment?.order?.id && phase === 'success' && (
          <button type="button" className="checkout-success-btn" onClick={() => navigate(`/order-confirmation/${payment.order.id}`)}>
            Ouvrir la confirmation
          </button>
        )}
      </section>
    </main>
  );
};

export default CheckoutSuccess;
