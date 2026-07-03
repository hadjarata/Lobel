import React, { useEffect, useRef } from 'react';
import { PROFILE_NAV_ITEMS } from './profileNavConfig';

const ProfileMobileNav = ({ activeTab, onTabChange, stats }) => {
  const navRef = useRef(null);
  const activeRef = useRef(null);

  useEffect(() => {
    activeRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'center',
    });
  }, [activeTab]);

  return (
    <nav className="profile-mobile-nav" aria-label="Navigation profil mobile" ref={navRef}>
      <div className="profile-mobile-nav-track">
        {PROFILE_NAV_ITEMS.map((item) => {
          const badge =
            (item.id === 'orders' && stats.ordersCount > 0 && stats.ordersCount) ||
            (item.id === 'cart' && stats.cartCount > 0 && stats.cartCount) ||
            null;

          return (
            <button
              key={item.id}
              type="button"
              ref={activeTab === item.id ? activeRef : null}
              className={`profile-mobile-nav-item${activeTab === item.id ? ' is-active' : ''}`}
              onClick={() => onTabChange(item.id)}
              aria-current={activeTab === item.id ? 'page' : undefined}
            >
              <span className="profile-mobile-nav-icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="profile-mobile-nav-label">{item.shortLabel}</span>
              {badge != null && <span className="profile-mobile-nav-badge">{badge}</span>}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default ProfileMobileNav;
