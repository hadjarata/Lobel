import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateLogin, validateRegister } from '../../services/authService';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register, loading } = useAuth();
  
  // États pour les formulaires
  const [activeForm, setActiveForm] = useState('login'); // 'login' ou 'register'
  const [loginData, setLoginData] = useState({
    email: '',
    password: ''
  });
  const [registerData, setRegisterData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: ''
  });
  
  // États pour les erreurs
  const [loginErrors, setLoginErrors] = useState({});
  const [registerErrors, setRegisterErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  // Gérer les changements dans le formulaire de login
  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({ ...prev, [name]: value }));
    // Effacer l'erreur quand l'utilisateur tape
    if (loginErrors[name]) {
      setLoginErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Gérer les changements dans le formulaire d'inscription
  const handleRegisterChange = (e) => {
    const { name, value } = e.target;
    setRegisterData(prev => ({ ...prev, [name]: value }));
    // Effacer l'erreur quand l'utilisateur tape
    if (registerErrors[name]) {
      setRegisterErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // Soumettre le formulaire de login
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');

    // Validation
    const validation = validateLogin(loginData);
    if (!validation.isValid) {
      setLoginErrors(validation.errors);
      return;
    }

    // Tentative de login
    const result = await login(loginData);
    if (!result.success) {
      setSubmitError(result.error);
    }
  };

  // Soumettre le formulaire d'inscription
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');

    // Validation
    const validation = validateRegister(registerData);
    if (!validation.isValid) {
      setRegisterErrors(validation.errors);
      return;
    }

    // Tentative d'inscription
    const result = await register(registerData);
    if (!result.success) {
      setSubmitError(result.error);
    }
  };

  // Message d'accueil basé sur la page d'origine
  const getWelcomeMessage = () => {
    const from = location.state?.from?.pathname;
    if (from && from.includes('/product/')) {
      return "Connectez-vous pour continuer vos achats";
    }
    if (from && from === '/cart') {
      return "Connectez-vous pour finaliser votre panier";
    }
    return "Bienvenue sur Lobel Store";
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        {/* Message d'accueil mobile */}
        <div className="auth-welcome-mobile">
          <h1>{getWelcomeMessage()}</h1>
        </div>

        <div className="auth-split">
          {/* LEFT: LOGIN */}
          <div className={`auth-section ${activeForm === 'login' ? 'active' : ''}`}>
            <div className="auth-form-container">
              <div className="auth-header">
                <h2>Connexion</h2>
                <p>Bon retour parmi nous !</p>
              </div>

              <form onSubmit={handleLoginSubmit} className="auth-form">
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    className={`form-input ${loginErrors.email ? 'error' : ''}`}
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
                    onChange={handleLoginChange}
                    className={`form-input ${loginErrors.password ? 'error' : ''}`}
                    placeholder="Votre mot de passe"
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

              {/* Switch vers register (mobile) */}
              <div className="auth-switch-mobile">
                <p>
                  Pas encore de compte ?{' '}
                  <button
                    type="button"
                    onClick={() => setActiveForm('register')}
                    className="switch-btn"
                  >
                    Créer un compte
                  </button>
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT: REGISTER */}
          <div className={`auth-section ${activeForm === 'register' ? 'active' : ''}`}>
            <div className="auth-form-container">
              <div className="auth-header">
                <h2>Inscription</h2>
                <p>Rejoignez-nous dès maintenant !</p>
              </div>

              <form onSubmit={handleRegisterSubmit} className="auth-form">
                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="first_name">Nom</label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={registerData.first_name}
                      onChange={handleRegisterChange}
                      className={`form-input ${registerErrors.first_name ? 'error' : ''}`}
                      placeholder="Votre nom"
                      disabled={loading}
                    />
                    {registerErrors.first_name && (
                      <span className="error-message">{registerErrors.first_name}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="last_name">Prénom</label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={registerData.last_name}
                      onChange={handleRegisterChange}
                      className={`form-input ${registerErrors.last_name ? 'error' : ''}`}
                      placeholder="Votre prénom"
                      disabled={loading}
                    />
                    {registerErrors.last_name && (
                      <span className="error-message">{registerErrors.last_name}</span>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="register_email">Email</label>
                  <input
                    type="email"
                    id="register_email"
                    name="email"
                    value={registerData.email}
                    onChange={handleRegisterChange}
                    className={`form-input ${registerErrors.email ? 'error' : ''}`}
                    placeholder="votre@email.com"
                    disabled={loading}
                  />
                  {registerErrors.email && (
                    <span className="error-message">{registerErrors.email}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="register_password">Mot de passe</label>
                  <input
                    type="password"
                    id="register_password"
                    name="password"
                    value={registerData.password}
                    onChange={handleRegisterChange}
                    className={`form-input ${registerErrors.password ? 'error' : ''}`}
                    placeholder="Min 8 caractères"
                    disabled={loading}
                  />
                  {registerErrors.password && (
                    <span className="error-message">{registerErrors.password}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="confirm_password">Confirmer le mot de passe</label>
                  <input
                    type="password"
                    id="confirm_password"
                    name="confirm_password"
                    value={registerData.confirm_password}
                    onChange={handleRegisterChange}
                    className={`form-input ${registerErrors.confirm_password ? 'error' : ''}`}
                    placeholder="Confirmez votre mot de passe"
                    disabled={loading}
                  />
                  {registerErrors.confirm_password && (
                    <span className="error-message">{registerErrors.confirm_password}</span>
                  )}
                </div>

                <button
                  type="submit"
                  className="auth-submit-btn"
                  disabled={loading}
                >
                  {loading ? 'Inscription...' : 'Créer un compte'}
                </button>
              </form>

              {/* Switch vers login (mobile) */}
              <div className="auth-switch-mobile">
                <p>
                  Déjà un compte ?{' '}
                  <button
                    type="button"
                    onClick={() => setActiveForm('login')}
                    className="switch-btn"
                  >
                    Se connecter
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Message d'erreur global */}
        {submitError && (
          <div className="auth-error-global">
            <span>{submitError}</span>
          </div>
        )}

        {/* Tabs pour mobile */}
        <div className="auth-tabs">
          <button
            className={`tab-btn ${activeForm === 'login' ? 'active' : ''}`}
            onClick={() => setActiveForm('login')}
          >
            Connexion
          </button>
          <button
            className={`tab-btn ${activeForm === 'register' ? 'active' : ''}`}
            onClick={() => setActiveForm('register')}
          >
            Inscription
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
