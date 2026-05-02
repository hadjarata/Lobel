import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { resetPassword, validateResetPassword } from '../../api/auth';
import './Auth.css';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const uid = searchParams.get('uid');
  const token = searchParams.get('token');

  useEffect(() => {
    if (!uid || !token) {
      setError('Le lien de réinitialisation est invalide ou incomplet.');
    }
  }, [uid, token]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage('');
    setError('');

    const validation = validateResetPassword({ password, confirm_password: confirmPassword });
    if (!validation.isValid) {
      setError(Object.values(validation.errors)[0]);
      return;
    }

    try {
      setLoading(true);
      await resetPassword({ uid, token, password, confirm_password: confirmPassword });
      setMessage('Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter.');
      setTimeout(() => {
        navigate('/login', { state: { message: 'Votre mot de passe a été réinitialisé. Connectez-vous.' } });
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Impossible de réinitialiser le mot de passe.');
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
          <h1>Réinitialiser le mot de passe</h1>
          <p>Entrez un nouveau mot de passe pour votre compte.</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {message && <div className="auth-success">{message}</div>}
          {error && <div className="auth-error">{error}</div>}

          <div className="form-group">
            <label htmlFor="password">Nouveau mot de passe</label>
            <input
              type="password"
              id="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="•••••••"
              disabled={loading || !!error && !uid}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmer le mot de passe</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="•••••••"
              disabled={loading || !!error && !uid}
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading || !!error && !uid}>
            {loading ? 'Traitement...' : 'Réinitialiser'}
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

export default ResetPassword;
