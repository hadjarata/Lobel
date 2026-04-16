import React from 'react';
import { useAuth } from '../../context/AuthContext';
import './AddToCartButton.css';

const AddToCartButton = ({ 
  children = 'Ajouter au panier',
  className = '',
  disabled = false,
  onClick,
  variant = 'primary' // primary, secondary, outline
}) => {
  const { requireAuth, isAuthenticated } = useAuth();

  const handleClick = (e) => {
    // Protection du panier - vérifier l'authentification
    if (!isAuthenticated) {
      e.preventDefault();
      requireAuth();
      return;
    }

    // Si authentifié, exécuter le onClick personnalisé
    if (onClick) {
      onClick(e);
    }
  };

  const buttonClass = `add-to-cart-btn ${variant} ${className} ${!isAuthenticated ? 'requires-auth' : ''}`;

  return (
    <button
      className={buttonClass}
      onClick={handleClick}
      disabled={disabled}
      title={!isAuthenticated ? 'Connectez-vous pour ajouter au panier' : ''}
    >
      {children}
    </button>
  );
};

export default AddToCartButton;
