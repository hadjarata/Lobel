import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateLogin } from '../../api/auth';
import './Auth.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loading, user } = useAuth();

  // Afficher le message de redirection et gérer la redirection automatique
  useEffect(() => {
    // Afficher le message s'il vient d'une redirection
    if (location.state?.message) {
      setInfoMessage(location.state.message);
    }

    // Redirection automatique si déjà connecté
    if (user) {
      const from = location.state?.from?.pathname || '/shop';
      navigate(from, { replace: true });
    }
  }, [user, navigate, location]);
  
  // États pour le formulaire de login
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });
  
  // États pour les erreurs
  const [loginErrors, setLoginErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  // Gérer les changements dans le formulaire
  const handleChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({ ...prev, [name]: value }));
    // Effacer l'erreur quand l'utilisateur tape
    if (loginErrors[name]) {
      setLoginErrors(prev => ({ ...prev, [name]: '' }));
    }
    // Effacer l'erreur générale
    if (submitError) {
      setSubmitError('');
    }
  };

  // Soumettre le formulaire de login
  const handleSubmit = async (e) => {
  e.preventDefault();

  if (loading) return;

  const validation = validateLogin(loginData);
  if (!validation.isValid) {
    setLoginErrors(validation.errors);
    return;
  }

  try {
    await login(loginData);
  } catch (error) {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      'Email ou mot de passe incorrect';

    setSubmitError(message);
  }
};

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h2>Lobel Store</h2>
        </div>
        <div className="auth-header">
          <h1>Connexion</h1>
          <p>Accédez à votre compte</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {infoMessage && (
            <div className="auth-info">
              {infoMessage}
            </div>
          )}
          
          {submitError && (
            <div className="auth-error">
              {submitError}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={loginData.email}
              onChange={handleChange}
              className={loginErrors.email ? 'error' : ''}
              placeholder="votre@email.com"
              disabled={loading}
            />
            {loginErrors.email && (
              <span className="error-message">{loginErrors.email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              name="password"
              value={loginData.password}
              onChange={handleChange}
              className={loginErrors.password ? 'error' : ''}
              placeholder="••••••••"
              disabled={loading}
            />
            {loginErrors.password && (
              <span className="error-message">{loginErrors.password}</span>
            )}
          </div>

          <button 
            type="submit" 
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Vous n'avez pas de compte ?{' '}
            <Link to="/register" className="auth-link">
              S'inscrire
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
