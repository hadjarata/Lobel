import React from 'react';
import './Profile.css';

const Profile = () => {
  return (
    <div className="profile-page">
      <div className="profile-container">
        <h1>Mon Profil</h1>
        <div className="profile-content">
          <div className="profile-section">
            <h2>Informations personnelles</h2>
            <div className="profile-info">
              <p>Nom: Utilisateur</p>
              <p>Email: utilisateur@example.com</p>
            </div>
          </div>
          
          <div className="profile-section">
            <h2>Commandes récentes</h2>
            <div className="orders-list">
              <p>Aucune commande récente</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
