import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getOrders } from '../../api/orders';
import { getOrderStatus } from '../../orders/orderPolicy';
import { formatDate, formatPrice } from '../../utils/profileUtils';
import './Orders.css';

const OrdersList = () => {
  const [params, setParams] = useSearchParams();
  const [page, setPage] = useState(null);
  const [error, setError] = useState('');
  const requestId = useRef(0);
  const pageNumber = Math.max(1, Number(params.get('page')) || 1);
  const status = params.get('status') || '';
  const ordering = params.get('ordering') || '-date_ordered';

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    getOrders({ page: pageNumber, status, ordering }, { signal: controller.signal })
      .then((result) => {
        if (id !== requestId.current) return;
        setError('');
        setPage(result);
        if (!result.results.length && pageNumber > 1) {
          setParams((current) => {
            current.set('page', '1');
            return current;
          }, { replace: true });
        }
      })
      .catch((err) => {
        if (err?.name !== 'CanceledError' && id === requestId.current) {
          setError('Impossible de charger vos commandes.');
        }
      });
    return () => controller.abort();
  }, [pageNumber, status, ordering, setParams]);

  const update = (key, value) => setParams((current) => {
    if (value) current.set(key, value); else current.delete(key);
    if (key !== 'page') current.set('page', '1');
    return current;
  });

  return (
    <main className="orders-page">
      <h1>Mes commandes</h1>
      <div className="orders-toolbar">
        <label>Statut <select value={status} onChange={(e) => update('status', e.target.value)}>
          <option value="">Tous</option>
          <option value="pending_payment">À payer</option>
          <option value="payment_processing">Paiement en vérification</option>
          <option value="paid">Payées</option>
          <option value="preparing">En préparation</option>
          <option value="shipped">Expédiées</option>
          <option value="delivered">Livrées</option>
          <option value="cancelled">Annulées</option>
        </select></label>
        <label>Tri <select value={ordering} onChange={(e) => update('ordering', e.target.value)}>
          <option value="-date_ordered">Plus récentes</option>
          <option value="date_ordered">Plus anciennes</option>
        </select></label>
      </div>
      {!page && !error && <p role="status">Chargement des commandes…</p>}
      {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => update('ordering', ordering)}>Réessayer</button></div>}
      {page?.results.length === 0 && <p>Aucune commande ne correspond à ces critères.</p>}
      <ul className="orders-list">
        {page?.results.map((order) => {
          const state = getOrderStatus(order.status);
          return <li key={order.id}><article className="orders-card">
            <div className="orders-card-head"><div><strong>Commande #{order.id}</strong><p>{formatDate(order.date_ordered)}</p></div>
              <span className="order-status" data-tone={state.tone}>{state.label}</span></div>
            <p>{order.item_count ?? order.cart_items} article(s) — {formatPrice(order.total_amount ?? order.cart_total)} {order.currency}</p>
            <div className="orders-actions"><Link to={`/account/orders/${order.id}`}>Voir le détail</Link>
              {order.can_pay && <Link to="/checkout">Reprendre le paiement</Link>}</div>
          </article></li>;
        })}
      </ul>
      {page && <nav className="orders-pagination" aria-label="Pagination des commandes">
        <button type="button" disabled={!page.previous} onClick={() => update('page', String(pageNumber - 1))}>Précédente</button>
        <span>Page {pageNumber}</span>
        <button type="button" disabled={!page.next} onClick={() => update('page', String(pageNumber + 1))}>Suivante</button>
      </nav>}
    </main>
  );
};

export default OrdersList;
