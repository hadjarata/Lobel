import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  cancelOrder, downloadOrderReceipt, getOrderById,
} from '../../api/orders';
import { getOrderStatus } from '../../orders/orderPolicy';
import { formatDateTime, formatPrice } from '../../utils/profileUtils';
import './Orders.css';

const OrderDetail = ({ confirmation = false }) => {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const dialogRef = useRef(null);

  const load = async (signal) => {
    setError('');
    try {
      setOrder(await getOrderById(id, signal ? { signal } : {}));
    } catch (err) {
      if (err?.name !== 'CanceledError') {
        setError(err?.response?.status === 404
          ? 'Cette commande est introuvable.'
          : 'Impossible de charger cette commande.');
      }
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    const refresh = () => load(controller.signal);
    window.addEventListener('focus', refresh);
    return () => {
      controller.abort();
      window.removeEventListener('focus', refresh);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const submitCancellation = async (event) => {
    event.preventDefault();
    if (busy) return;
    const reason = new FormData(event.currentTarget).get('reason')?.trim();
    if (!reason) return;
    setBusy(true);
    try {
      setOrder(await cancelOrder(id, reason));
      dialogRef.current?.close();
    } catch {
      setError('Cette commande ne peut pas être annulée pour le moment.');
    } finally {
      setBusy(false);
    }
  };

  const receipt = async () => {
    if (busy) return;
    setBusy(true);
    let url;
    try {
      const result = await downloadOrderReceipt(id);
      url = URL.createObjectURL(result.blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = result.filename;
      anchor.click();
    } catch {
      setError('Le justificatif est temporairement indisponible.');
    } finally {
      if (url) URL.revokeObjectURL(url);
      setBusy(false);
    }
  };

  if (!order && !error) return <main className="orders-page"><p role="status">Chargement de la commande…</p></main>;
  if (error && !order) return <main className="orders-page"><div role="alert"><p>{error}</p><button type="button" onClick={() => load()}>Réessayer</button></div></main>;
  const state = getOrderStatus(order.status);

  return <main className="orders-page">
    <Link to="/account/orders">← Mes commandes</Link>
    <section className="order-detail-card" aria-live="polite">
      <h1>{confirmation ? 'Confirmation de commande' : `Commande #${order.id}`}</h1>
      {error && <p role="alert">{error}</p>}
      <p><strong>Commande #{order.id}</strong> — {formatDateTime(order.date_ordered)}</p>
      <p className="order-status" data-tone={state.tone}>{state.label}</p>
      {confirmation && order.payment?.status !== 'completed'
        && <p>Le paiement est encore en cours de vérification. Aucun nouveau paiement n’est nécessaire.</p>}

      <h2>Suivi</h2>
      <ol className="order-timeline">
        {order.timeline.map((event) => <li key={`${event.code}-${event.occurred_at}`}>
          <strong>{event.label}</strong><br /><time>{formatDateTime(event.occurred_at)}</time>
        </li>)}
      </ol>

      <h2>Articles</h2>
      <table className="order-items"><thead><tr><th>Article</th><th>Variante</th><th>Quantité</th><th>Prix</th><th>Total</th></tr></thead>
        <tbody>{order.items.map((item) => <tr key={item.id}><td>{item.product_name}</td>
          <td>{item.variant_name || '—'}</td><td>{item.quantity}</td>
          <td>{formatPrice(item.unit_price)} {item.currency}</td>
          <td>{formatPrice(item.line_total)} {item.currency}</td></tr>)}</tbody></table>

      <h2>Livraison</h2>
      <address>{order.delivery_recipient_name}<br />{order.delivery_address}</address>
      <p>{order.delivery_method_label}</p>

      <div className="order-totals">
        <div><span>Sous-total</span><strong>{formatPrice(order.subtotal_amount)} {order.currency}</strong></div>
        <div><span>Livraison</span><strong>{formatPrice(order.shipping_amount)} {order.currency}</strong></div>
        <div><span>Réduction</span><strong>{formatPrice(order.discount_amount)} {order.currency}</strong></div>
        <div><span>Total</span><strong>{formatPrice(order.total_amount)} {order.currency}</strong></div>
      </div>
      <div className="orders-actions">
        {order.available_actions.can_download_receipt
          && <button type="button" disabled={busy} onClick={receipt}>
            {busy ? 'Téléchargement…' : 'Télécharger le justificatif PDF'}
          </button>}
        {order.available_actions.can_pay && <Link to="/checkout">Reprendre le paiement</Link>}
        {order.available_actions.can_cancel
          && <button type="button" onClick={() => dialogRef.current?.showModal()}>Annuler la commande</button>}
        <a href={`mailto:support@lobelstore.example?subject=Commande%20${encodeURIComponent(order.id)}`}>Contacter le support</a>
      </div>
    </section>
    <dialog ref={dialogRef} className="order-dialog" onClose={() => setError('')}>
      <form onSubmit={submitCancellation}>
        <h2>Annuler la commande</h2>
        <label>Motif<textarea name="reason" required minLength="3" maxLength="500" autoFocus /></label>
        <div className="orders-actions"><button type="button" onClick={() => dialogRef.current?.close()}>Retour</button>
          <button type="submit" disabled={busy}>Confirmer l’annulation</button></div>
      </form>
    </dialog>
  </main>;
};

export default OrderDetail;
