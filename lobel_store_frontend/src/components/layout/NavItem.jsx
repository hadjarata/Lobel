import React from 'react';
import { NavLink } from 'react-router-dom';
import './Navbar.css';

const NavItem = ({ 
  to, 
  icon: Icon, 
  children, 
  onClick,
  className = '',
  badge,
  isButton = false,
  end = false,
}) => {
  if (isButton) {
    return (
      <button type="button" className={`nav-item ${className}`} onClick={onClick}>
        {Icon && <Icon size={20} aria-hidden="true" />}
        <span className="nav-item-text">{children}</span>
        {badge && <span className="nav-item-badge">{badge}</span>}
      </button>
    );
  }

  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) => [
        'nav-item',
        className,
        isActive ? 'nav-item-active' : '',
      ].filter(Boolean).join(' ')}
    >
      {Icon && <Icon size={20} aria-hidden="true" />}
      <span className="nav-item-text">{children}</span>
      {badge && <span className="nav-item-badge">{badge}</span>}
    </NavLink>
  );
};

export default NavItem;
