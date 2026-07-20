import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/authState';
import { validatePassword } from '../../api/auth';

const ProfileSettingsPanel = () => {
  const { changePassword, logout, operationPending } = useAuth();
  const [passwords, setPasswords] = useState({
    current_password: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');

  const update = ({ target: { name, value } }) => {
    setPasswords((previous) => ({ ...previous, [name]: value }));
    setError('');
  };

  const submitPassword = async (event) => {
    event.preventDefault();
    if (operationPending) return;
    const validation = validatePassword(passwords.password, passwords.confirm_password);
    if (!passwords.current_password) validation.errors.current_password = 'Le mot de passe actuel est requis';
    if (Object.keys(validation.errors).length) {
      setError(Object.values(validation.errors)[0]);
      return;
    }
    try {
      await changePassword(passwords);
      setPasswords({ current_password: '', password: '', confirm_password: '' });
    } catch (requestError) {
      setError(requestError.fieldErrors?.current_password || requestError.message);
    }
  };

  return (
    <section className="profile-panel">
      <div className="profile-panel-head">
        <div>
          <h2 className="profile-panel-title">Paramètres</h2>
          <p className="profile-panel-subtitle">Sécurité du compte et préférences de session.</p>
        </div>
      </div>
      <div className="profile-settings-list">
        <article className="profile-settings-card">
          <form onSubmit={submitPassword} className="auth-form">
            <h3>Changer le mot de passe</h3>
            <p>Au moins 10 caractères. Les contrôles Django restent définitifs.</p>
            {error && <div className="auth-error">{error}</div>}
            <input type="password" name="current_password" aria-label="Mot de passe actuel" placeholder="Mot de passe actuel" value={passwords.current_password} onChange={update} disabled={operationPending} />
            <input type="password" name="password" aria-label="Nouveau mot de passe" placeholder="Nouveau mot de passe" value={passwords.password} onChange={update} disabled={operationPending} />
            <input type="password" name="confirm_password" aria-label="Confirmer le mot de passe" placeholder="Confirmer le mot de passe" value={passwords.confirm_password} onChange={update} disabled={operationPending} />
            <button type="submit" className="profile-btn profile-btn-outline profile-btn-small" disabled={operationPending}>
              Modifier le mot de passe
            </button>
          </form>
        </article>
        <article className="profile-settings-card">
          <div><h3>Boutique</h3><p>Retournez sur la boutique pour découvrir nos nouveautés.</p></div>
          <Link to="/shop" className="profile-btn profile-btn-outline profile-btn-small">Aller à la boutique</Link>
        </article>
        <article className="profile-settings-card profile-settings-card-danger">
          <div><h3>Déconnexion</h3><p>Fermez votre session sur cet appareil.</p></div>
          <button type="button" className="profile-btn profile-btn-danger profile-btn-small" onClick={logout} disabled={operationPending}>
            Se déconnecter
          </button>
        </article>
      </div>
    </section>
  );
};

export default ProfileSettingsPanel;
