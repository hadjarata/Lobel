import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../../context/authState';
import { validateLogin } from '../../api/auth';
import { parseApiError } from '../../utils/apiErrors';
import AuthPageShell from '../../components/auth/AuthPageShell';
import './Auth.css';

const Login = () => {
  const location = useLocation();
  const { login, loading } = useAuth();
  const infoMessage = location.state?.message || '';
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
  });
  const [loginErrors, setLoginErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

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
      setLoginData((previous) => ({ ...previous, password: '' }));
    } catch (error) {
      const parsed = parseApiError(error, 'Email ou mot de passe incorrect');
      setSubmitError(error.message || parsed.message);
    }
  };

  return (
    <AuthPageShell
      eyebrow="Espace privé"
      title="Connexion"
      description="Retrouvez vos commandes, vos favoris et votre sélection personnelle."
      note="Une expérience pensée pour révéler votre style, jusque dans les moindres détails."
    >
        <form onSubmit={handleSubmit} className="auth-entry-form" noValidate>
          {infoMessage && <div className="auth-info" role="status">{infoMessage}</div>}

          {submitError && <div className="auth-error" role="alert">{submitError}</div>}

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
              autoComplete="email"
              aria-invalid={Boolean(loginErrors.email)}
              aria-describedby={loginErrors.email ? 'login-email-error' : undefined}
            />
            {loginErrors.email && (
              <span className="error-message" id="login-email-error">{loginErrors.email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <div className="auth-password-field">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={loginData.password}
                onChange={handleChange}
                className={loginErrors.password ? 'error' : ''}
                placeholder="••••••••"
                disabled={loading}
                autoComplete="current-password"
                aria-invalid={Boolean(loginErrors.password)}
                aria-describedby={loginErrors.password ? 'login-password-error' : undefined}
              />
              <button
                type="button"
                className="auth-password-toggle"
                onClick={() => setShowPassword((visible) => !visible)}
                aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                aria-pressed={showPassword}
                disabled={loading}
              >
                {showPassword ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
              </button>
            </div>
            {loginErrors.password && (
              <span className="error-message" id="login-password-error">{loginErrors.password}</span>
            )}
          </div>

          <div className="auth-entry-form-meta">
            <Link to="/forgot-password" className="auth-link">Mot de passe oublié ?</Link>
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading} aria-busy={loading}>
            {loading ? 'Connexion en cours…' : 'Se connecter'}
          </button>
        </form>

        <footer className="auth-footer">
          <p>
            Vous n&apos;avez pas encore de compte ?{' '}
            <Link to="/register" className="auth-link">
              Créer un compte
            </Link>
          </p>
        </footer>
    </AuthPageShell>
  );
};

export default Login;
