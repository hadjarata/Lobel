import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const ProfileSettingsPanel = () => {
  const { logout } = useAuth();

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Paramètres</h2>
          <p className="profile-panel-subtitle">
            Sécurité du compte et préférences de session.
          </p>
        </div>
      </div>

      <div className="profile-settings-list">
        <article className="profile-settings-card">
          <div>
            <h3>Mot de passe</h3>
            <p>Réinitialisez votre mot de passe par e-mail en toute sécurité.</p>
          </div>
          <Link to="/forgot-password" className="profile-btn profile-btn-outline profile-btn-small">
            Changer le mot de passe
          </Link>
        </article>

        <article className="profile-settings-card">
          <div>
            <h3>Boutique</h3>
            <p>Retournez sur la boutique pour découvrir nos nouveautés.</p>
          </div>
          <Link to="/shop" className="profile-btn profile-btn-outline profile-btn-small">
            Aller à la boutique
          </Link>
        </article>

        <article className="profile-settings-card profile-settings-card-danger">
          <div>
            <h3>Déconnexion</h3>
            <p>Fermez votre session sur cet appareil.</p>
          </div>
          <button type="button" className="profile-btn profile-btn-danger profile-btn-small" onClick={logout}>
            Se déconnecter
          </button>
        </article>
      </div>
    </section>
  );
};

export default ProfileSettingsPanel;
