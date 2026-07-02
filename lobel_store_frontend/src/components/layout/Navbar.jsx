import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  Home, 
  ShoppingBag, 
  User, 
  ShoppingCart, 
  LogOut 
} from 'lucide-react';
import NavItem from './NavItem';
import './Navbar.css';

const Navbar = () => {
  const { isAuthenticated, logout } = useAuth();
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    // Charger le compteur du panier depuis le localStorage
    const savedCount = localStorage.getItem('cartCount');
    if (savedCount) {
      setCartCount(parseInt(savedCount));
    }

    // Écouter les mises à jour du panier
    const handleCartUpdate = () => {
      const currentCount = localStorage.getItem('cartCount');
      setCartCount(currentCount ? parseInt(currentCount) : 0);
    };

    window.addEventListener('cartUpdated', handleCartUpdate);
    window.addEventListener('storage', handleCartUpdate);

    return () => {
      window.removeEventListener('cartUpdated', handleCartUpdate);
      window.removeEventListener('storage', handleCartUpdate);
    };
  }, []);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <div className="navbar-logo">
          <Link to="/" className="logo-link">
            <img src="/logo.jpg" alt="Lobel Store" className="logo-image" />
          </Link>
        </div>

        {/* Navigation principale - une seule barre */}
        <div className="navbar-nav">
          {/* Navigation de base (toujours visible) */}
          <NavItem to="/" icon={Home}>Accueil</NavItem>
          <NavItem to="/shop" icon={ShoppingBag}>Boutique</NavItem>

          {/* Navigation conditionnelle selon auth */}
          {isAuthenticated ? (
            <>
              <NavItem to="/cart" icon={ShoppingCart} badge={cartCount > 0 ? cartCount : null}>
                Panier
              </NavItem>
              <NavItem to="/profile" icon={User}>Profil</NavItem>
            </>
          ) : null}
        </div>

        {/* Boutons à droite */}
        <div className="navbar-right">
          {isAuthenticated ? (
            <div className="navbar-logout">
              <NavItem 
                icon={LogOut} 
                onClick={logout}
                isButton={true}
                className="logout-item"
              >
                Déconnexion
              </NavItem>
            </div>
          ) : (
            <div className="navbar-login">
              <NavItem to="/login" icon={User} className="login-item">
                Connexion
              </NavItem>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
