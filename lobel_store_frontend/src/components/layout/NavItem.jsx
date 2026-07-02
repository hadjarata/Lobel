import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

const NavItem = ({ 
  to, 
  icon: Icon, 
  children, 
  onClick,
  className = '',
  badge,
  isButton = false 
}) => {
  const Component = isButton ? 'button' : Link;
  const props = isButton ? { onClick } : { to, onClick };

  return (
    <Component 
      className={`nav-item ${className}`}
      {...props}
    >
      {Icon && <Icon size={20} />}
      <span className="nav-item-text">{children}</span>
      {badge && <span className="nav-item-badge">{badge}</span>}
    </Component>
  );
};

export default NavItem;
