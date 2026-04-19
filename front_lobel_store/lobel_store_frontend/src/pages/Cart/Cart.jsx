import React from 'react';
import './Cart.css';

const Cart = () => {
  return (
    <div className="cart-page">
      <div className="cart-container">
        <h1>Mon Panier</h1>
        <div className="cart-content">
          <div className="cart-empty">
            <p>Votre panier est vide</p>
            <button className="continue-shopping-btn">
              Continuer mes achats
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cart;
