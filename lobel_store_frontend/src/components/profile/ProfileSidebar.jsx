import React from 'react';
import { PROFILE_NAV_ITEMS } from './profileNavConfig';

const ProfileSidebar = ({ activeTab, onTabChange, stats }) => {
  return (
    <nav className="profile-sidebar profile-sidebar-desktop" aria-label="Navigation profil">
      <ul className="profile-nav-list">
        {PROFILE_NAV_ITEMS.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`profile-nav-item${activeTab === item.id ? ' is-active' : ''}`}
              onClick={() => onTabChange(item.id)}
            >
              <span className="profile-nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="profile-nav-label">{item.label}</span>
              {item.id === 'orders' && stats.ordersCount > 0 && (
                <span className="profile-nav-badge">{stats.ordersCount}</span>
              )}
              {item.id === 'cart' && stats.cartCount > 0 && (
                <span className="profile-nav-badge">{stats.cartCount}</span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default ProfileSidebar;
