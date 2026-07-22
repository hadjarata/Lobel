import React, { useState } from 'react';
import { useAuth } from '../../context/authState';
import { validatePassword } from '../../api/auth';

const ProfileSettingsPanel = () => {
  const { changePassword, operationPending } = useAuth();
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
            <label className="profile-field">
              <span>Mot de passe actuel</span>
              <input type="password" name="current_password" value={passwords.current_password} onChange={update} disabled={operationPending} />
            </label>
            <label className="profile-field">
              <span>Nouveau mot de passe</span>
              <input type="password" name="password" value={passwords.password} onChange={update} disabled={operationPending} />
            </label>
            <label className="profile-field">
              <span>Confirmer le mot de passe</span>
              <input type="password" name="confirm_password" value={passwords.confirm_password} onChange={update} disabled={operationPending} />
            </label>
            <button type="submit" className="profile-btn profile-btn-outline profile-btn-small" disabled={operationPending}>
              Modifier le mot de passe
            </button>
          </form>
        </article>
        <article className="profile-settings-card profile-settings-card-danger">
          <div>
            <h3>Suppression du compte</h3>
            <p>Cette action sera disponible lorsque la suppression sécurisée du compte sera activée.</p>
          </div>
          <button type="button" className="profile-btn profile-btn-danger profile-btn-small" disabled>
            Supprimer mon compte
          </button>
        </article>
      </div>
    </section>
  );
};

export default ProfileSettingsPanel;
