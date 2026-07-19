import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  backdropVariants,
  panelVariants,
  sheetUpVariants,
  springModal,
  springSheet,
  springSnappy,
} from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import {
  formatDate,
  formatDateTime,
  formatPrice,
  getOrderStatusLabel,
} from '../../utils/profileUtils';
import { getProductImageUrl } from '../../utils/mediaUtils';

const ProfileOrdersPanel = ({ orders, loading, onRefresh, initialSelectedOrderId = null }) => {
  const [selectedOrderId, setSelectedOrderId] = useState(initialSelectedOrderId);
  const [isMobileSheet, setIsMobileSheet] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(max-width: 768px)').matches,
  );
  const selectedOrder = orders.find((order) => order.id === selectedOrderId);

  useEffect(() => {
    if (initialSelectedOrderId) {
      setSelectedOrderId(initialSelectedOrderId);
    }
  }, [initialSelectedOrderId]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(max-width: 768px)');
    const syncMobileSheet = () => setIsMobileSheet(mediaQuery.matches);

    syncMobileSheet();
    mediaQuery.addEventListener('change', syncMobileSheet);

    return () => mediaQuery.removeEventListener('change', syncMobileSheet);
  }, []);

  useEffect(() => {
    if (!selectedOrder) {
      return undefined;
    }

    const mediaQuery = window.matchMedia('(max-width: 768px)');

    const syncBodyLock = () => {
      if (mediaQuery.matches) {
        document.body.classList.add('profile-order-detail-open');
      } else {
        document.body.classList.remove('profile-order-detail-open');
      }
    };

    syncBodyLock();
    mediaQuery.addEventListener('change', syncBodyLock);

    return () => {
      mediaQuery.removeEventListener('change', syncBodyLock);
      document.body.classList.remove('profile-order-detail-open');
    };
  }, [selectedOrder]);

  const completedOrders = orders.filter((order) => order.complete || order.status === 'paid');

  const openOrderDetail = (orderId) => {
    setSelectedOrderId(orderId);
  };

  const closeOrderDetail = () => {
    setSelectedOrderId(null);
  };

  const overlayTransition = useMotionTransition(springModal);
  const sheetTransition = useMotionTransition(springSheet);
  const panelTransition = useMotionTransition(springSnappy);
  const detailVariants = isMobileSheet ? sheetUpVariants : panelVariants;
  const detailTransition = isMobileSheet ? sheetTransition : panelTransition;

  if (loading) {
    return (
      <section className="profile-panel">
        <div className="profile-loading-inline">
          <div className="profile-spinner" />
          <p>Chargement des commandes...</p>
        </div>
      </section>
    );
  }

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Mes commandes</h2>
          <p className="profile-panel-subtitle">
            Suivez l&apos;historique et le statut de vos achats.
          </p>
        </div>
        <button type="button" className="profile-btn profile-btn-ghost" onClick={onRefresh}>
          Actualiser
        </button>
      </div>

      <div className="profile-stats-row">
        <div className="profile-stat-card">
          <span className="profile-stat-value">{orders.length}</span>
          <span className="profile-stat-label">Total commandes</span>
        </div>
        <div className="profile-stat-card">
          <span className="profile-stat-value">{completedOrders.length}</span>
          <span className="profile-stat-label">Commandes payées</span>
        </div>
      </div>

      {orders.length === 0 ? (
        <div className="profile-empty-state">
          <p>Aucune commande pour le moment.</p>
        </div>
      ) : (
        <div className={`profile-orders-layout${selectedOrder ? ' has-detail' : ''}`}>
          <ul className="profile-order-list">
            {orders.map((order) => {
              const total = order.cart_total ?? 0;
              const itemsCount = order.cart_items ?? order.items?.length ?? 0;

              return (
                <li key={order.id}>
                  <article
                    className={`profile-order-card${
                      selectedOrderId === order.id ? ' is-selected' : ''
                    }`}
                  >
                    <div className="profile-order-card-top">
                      <div className="profile-order-card-title">
                        <p className="profile-order-id">Commande #{order.id}</p>
                        <p className="profile-order-date">{formatDate(order.date_ordered)}</p>
                      </div>
                      <span className={`profile-badge profile-badge-${order.status}`}>
                        {getOrderStatusLabel(order.status)}
                      </span>
                    </div>
                    <div className="profile-order-card-meta">
                      <span>{itemsCount} article{itemsCount > 1 ? 's' : ''}</span>
                      <strong>{formatPrice(total)} FCFA</strong>
                    </div>
                    <button
                      type="button"
                      className="profile-btn profile-btn-outline profile-btn-small profile-btn-block-mobile"
                      onClick={() => openOrderDetail(order.id)}
                    >
                      Voir détails
                    </button>
                  </article>
                </li>
              );
            })}
          </ul>

          <AnimatePresence>
            {selectedOrder && (
              <>
                <motion.button
                  type="button"
                  className="profile-order-detail-backdrop"
                  aria-label="Fermer le détail"
                  onClick={closeOrderDetail}
                  variants={isMobileSheet ? backdropVariants : undefined}
                  initial={isMobileSheet ? 'initial' : false}
                  animate={isMobileSheet ? 'animate' : undefined}
                  exit={isMobileSheet ? 'exit' : undefined}
                  transition={isMobileSheet ? overlayTransition : undefined}
                />
                <motion.aside
                  className="profile-order-detail"
                  role="dialog"
                  aria-modal="true"
                  variants={detailVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  transition={detailTransition}
                >
                <div className="profile-order-detail-head">
                  <button
                    type="button"
                    className="profile-order-detail-back profile-btn profile-btn-ghost profile-btn-small"
                    onClick={closeOrderDetail}
                  >
                    ← Retour
                  </button>
                  <h3>Commande #{selectedOrder.id}</h3>
                </div>

                <dl className="profile-detail-rows">
                  <div>
                    <dt>Date</dt>
                    <dd>{formatDateTime(selectedOrder.date_ordered)}</dd>
                  </div>
                  <div>
                    <dt>Statut</dt>
                    <dd>{getOrderStatusLabel(selectedOrder.status)}</dd>
                  </div>
                  <div>
                    <dt>Total</dt>
                    <dd>{formatPrice(selectedOrder.cart_total)} FCFA</dd>
                  </div>
                  {selectedOrder.transaction_id && (
                    <div>
                      <dt>Transaction</dt>
                      <dd className="profile-detail-break">{selectedOrder.transaction_id}</dd>
                    </div>
                  )}
                </dl>

                <ul className="profile-order-items">
                  {(selectedOrder.items || []).map((item) => {
                    const imageUrl = getProductImageUrl(item.product);
                    const lineTotal =
                      Number(item.product?.price || 0) * Number(item.quantity || 0);

                    return (
                      <li key={item.id} className="profile-order-item">
                        <div className="profile-order-item-media">
                          {imageUrl ? (
                            <img src={imageUrl} alt={item.product?.name || 'Produit'} />
                          ) : (
                            <span>LOBEL</span>
                          )}
                        </div>
                        <div className="profile-order-item-info">
                          <p>{item.product?.name || 'Produit'}</p>
                          <span>
                            {item.quantity} × {formatPrice(item.product?.price)} FCFA
                          </span>
                        </div>
                        <strong className="profile-order-item-price">
                          {formatPrice(lineTotal)} FCFA
                        </strong>
                      </li>
                    );
                  })}
                </ul>
                </motion.aside>
              </>
            )}
          </AnimatePresence>
        </div>
      )}
    </section>
  );
};

export default ProfileOrdersPanel;
