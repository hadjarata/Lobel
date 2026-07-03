import React from 'react';
import {
  getAccountStatus,
  getCustomerDisplayName,
  getCustomerInitials,
} from '../../utils/profileUtils';

const ProfileHeader = ({ customer, onEditProfile, compact = false }) => {
  if (!customer) {
    return null;
  }

  const displayName = getCustomerDisplayName(customer);
  const email = customer.user?.email || '—';
  const accountStatus = getAccountStatus(customer);

  return (
    <header className={`profile-header${compact ? ' profile-header-compact' : ''}`}>
      <div className="profile-header-main">
        <div className="profile-avatar" aria-hidden="true">
          {getCustomerInitials(customer)}
        </div>
        <div className="profile-header-info">
          {!compact && <p className="profile-eyebrow">Espace client</p>}
          <h1 className="profile-header-name">{displayName}</h1>
          {!compact && <p className="profile-header-email">{email}</p>}
          <span className={`profile-status-badge profile-status-${accountStatus.tone}`}>
            {accountStatus.label}
          </span>
        </div>
      </div>
      {!compact && (
        <button type="button" className="profile-btn profile-btn-outline profile-header-edit" onClick={onEditProfile}>
          Modifier le profil
        </button>
      )}
    </header>
  );
};

export default ProfileHeader;
