import React from 'react';
import { Link } from 'react-router-dom';
import { Home, LogOut, ShoppingBag, ShoppingCart, User } from 'lucide-react';
import { useCart } from '../../cart/cartState';
import { useAuth } from '../../context/authState';
import NavItem from './NavItem';
import './Navbar.css';

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const { itemCount } = useCart();
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <Link to="/" className="logo-link"><img src="/logo.jpg" alt="Lobel Store" className="logo-image" /></Link>
        </div>
        <div className="navbar-nav">
          <NavItem to="/" icon={Home} end>Accueil</NavItem>
          <NavItem to="/shop" icon={ShoppingBag}>Boutique</NavItem>
          <NavItem to="/cart" icon={ShoppingCart} badge={itemCount > 0 ? itemCount : null}>Panier</NavItem>
          {isAuthenticated && <NavItem to="/profile" icon={User}>Profil</NavItem>}
        </div>
        <div className="navbar-right">
          {isAuthenticated ? (
            <div className="navbar-logout">
              <NavItem icon={LogOut} onClick={logout} isButton className="logout-item">Déconnexion</NavItem>
            </div>
          ) : (
            <div className="navbar-login">
              <NavItem to="/login" icon={User} className="login-item">Connexion</NavItem>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
