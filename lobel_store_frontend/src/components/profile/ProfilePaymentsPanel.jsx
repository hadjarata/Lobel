import React from 'react';
import {
  formatDateTime,
  formatPrice,
  getPaymentMethodLabel,
  getPaymentStatusLabel,
} from '../../utils/profileUtils';

const ProfilePaymentsPanel = ({ payments, loading, onRefresh, onViewOrder }) => {
  if (loading) {
    return (
      <section className="profile-panel">
        <div className="profile-loading-inline">
          <div className="profile-spinner" />
          <p>Chargement des paiements...</p>
        </div>
      </section>
    );
  }

  const completedCount = payments.filter((payment) => payment.status === 'completed').length;

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Paiements</h2>
          <p className="profile-panel-subtitle">
            Historique de vos transactions et statuts de paiement.
          </p>
        </div>
        <button type="button" className="profile-btn profile-btn-ghost" onClick={onRefresh}>
          Actualiser
        </button>
      </div>

      <div className="profile-stats-row">
        <div className="profile-stat-card">
          <span className="profile-stat-value">{payments.length}</span>
          <span className="profile-stat-label">Transactions</span>
        </div>
        <div className="profile-stat-card">
          <span className="profile-stat-value">{completedCount}</span>
          <span className="profile-stat-label">Confirmés</span>
        </div>
      </div>

      {payments.length === 0 ? (
        <div className="profile-empty-state">
          <p>Aucun paiement enregistré.</p>
        </div>
      ) : (
        <ul className="profile-payment-list">
          {payments.map((payment) => (
            <li key={payment.id}>
              <article className="profile-payment-card">
                <div className="profile-payment-card-top">
                  <div>
                    <p className="profile-payment-id">Paiement #{payment.id}</p>
                    <p className="profile-payment-date">
                      {formatDateTime(payment.date_paid || payment.processed_at)}
                    </p>
                  </div>
                  <span className={`profile-badge profile-badge-${payment.status}`}>
                    {getPaymentStatusLabel(payment.status)}
                  </span>
                </div>

                <div className="profile-payment-card-body">
                  <div>
                    <span className="profile-payment-label">Montant</span>
                    <strong>{formatPrice(payment.amount)} {payment.currency || 'FCFA'}</strong>
                  </div>
                  <div>
                    <span className="profile-payment-label">Méthode</span>
                    <span>{getPaymentMethodLabel(payment.payment_method)}</span>
                  </div>
                  <div>
                    <span className="profile-payment-label">Commande</span>
                    {payment.order?.id ? (
                      <button
                        type="button"
                        className="profile-link-btn"
                        onClick={() => onViewOrder?.(payment.order.id)}
                      >
                        #{payment.order.id}
                      </button>
                    ) : (
                      <span>—</span>
                    )}
                  </div>
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default ProfilePaymentsPanel;
