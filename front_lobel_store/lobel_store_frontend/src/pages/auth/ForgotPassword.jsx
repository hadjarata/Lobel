import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { requestPasswordReset, validateEmailOnly } from '../../api/auth';
import './Auth.css';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setError('');

    const validation = validateEmailOnly(email);
    if (!validation.isValid) {
      setError(validation.errors.email);
      return;
    }

    try {
      setLoading(true);
      const data = await requestPasswordReset({ email });
      setMessage(data.detail || 'Si l’email existe, un lien de réinitialisation a été envoyé.');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Impossible de demander la réinitialisation du mot de passe.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h2>Lobel Store</h2>
        </div>
        <div className="auth-header">
          <h1>Mot de passe oublié</h1>
          <p>Entrez votre adresse email pour recevoir un lien de réinitialisation.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {message && <div className="auth-success">{message}</div>}
          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="votre@email.com"
              disabled={loading}
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Envoi en cours...' : 'Envoyer le lien'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Retour à la connexion {' '}
            <Link to="/login" className="auth-link">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
