import React from 'react';
import './Checkout.css';

const Checkout = () => {
  return (
    <div className="checkout-page">
      <div className="checkout-container">
        <h1>Finaliser la commande</h1>
        <div className="checkout-content">
          <div className="checkout-empty">
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

export default Checkout;
