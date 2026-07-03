import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateLogin } from '../../api/auth';
import { parseApiError } from '../../utils/apiErrors';
import logo from '../../logo/LOBEL PROFIL 4.jpg.jpeg';
import './Auth.css';

const Login = () => {
  const location = useLocation();
  const { login, loading } = useAuth();
  const [infoMessage, setInfoMessage] = useState('');
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
  });
  const [loginErrors, setLoginErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    if (location.state?.message) {
      setInfoMessage(location.state.message);
    }
  }, [location.state]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({ ...prev, [name]: value }));

    if (loginErrors[name]) {
      setLoginErrors((prev) => ({ ...prev, [name]: '' }));
    }

    if (submitError) {
      setSubmitError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) {
      return;
    }

    const validation = validateLogin(loginData);
    if (!validation.isValid) {
      setLoginErrors(validation.errors);
      return;
    }

    try {
      await login(loginData);
    } catch (error) {
      const parsed = parseApiError(error, 'Email ou mot de passe incorrect');
      setSubmitError(error.message || parsed.message);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <img src={logo} alt="Lobel Store logo" />
        </div>
        <div className="auth-header">
          <h1>Connexion</h1>
          <p>Accédez à votre compte</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {infoMessage && <div className="auth-info">{infoMessage}</div>}

          {submitError && <div className="auth-error">{submitError}</div>}

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

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            <Link to="/forgot-password" className="auth-link">
              Mot de passe oublié ?
            </Link>
          </p>
          <p>
            Vous n&apos;avez pas de compte ?{' '}
            <Link to="/register" className="auth-link">
              S&apos;inscrire
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
