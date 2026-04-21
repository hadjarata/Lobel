import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { validateRegister } from '../../api/auth';
import './Auth.css';

const Register = () => {
  const navigate = useNavigate();
  const { register, loading, user } = useAuth();

  // États pour le formulaire d'inscription
  const [registerData, setRegisterData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: ''
  });
  
  // États pour les erreurs
  const [registerErrors, setRegisterErrors] = useState({});
  const [submitError, setSubmitError] = useState('');

  // Gérer les changements dans le formulaire
  const handleChange = (e) => {
    const { name, value } = e.target;
    setRegisterData(prev => ({ ...prev, [name]: value }));
    // Effacer l'erreur quand l'utilisateur tape
    if (registerErrors[name]) {
      setRegisterErrors(prev => ({ ...prev, [name]: '' }));
    }
    // Effacer l'erreur générale
    if (submitError) {
      setSubmitError('');
    }
  };

  // Soumettre le formulaire d'inscription
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Valider les données
    const validation = validateRegister(registerData);
    if (!validation.isValid) {
      setRegisterErrors(validation.errors);
      return;
    }

    try {
      await register(registerData);
      // Redirection automatique gérée par AuthContext
    } catch (error) {
      setSubmitError(error.message || 'Erreur lors de l\'inscription');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h2>Lobel Store</h2>
        </div>
        <div className="auth-header">
          <h1>Inscription</h1>
          <p>Créez votre compte</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {submitError && (
            <div className="auth-error">
              {submitError}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="first_name">Prénom</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={registerData.first_name}
                onChange={handleChange}
                className={registerErrors.first_name ? 'error' : ''}
                placeholder="Jean"
                disabled={loading}
              />
              {registerErrors.first_name && (
                <span className="error-message">{registerErrors.first_name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Nom</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={registerData.last_name}
                onChange={handleChange}
                className={registerErrors.last_name ? 'error' : ''}
                placeholder="Dupont"
                disabled={loading}
              />
              {registerErrors.last_name && (
                <span className="error-message">{registerErrors.last_name}</span>
              )}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={registerData.email}
              onChange={handleChange}
              className={registerErrors.email ? 'error' : ''}
              placeholder="votre@email.com"
              disabled={loading}
            />
            {registerErrors.email && (
              <span className="error-message">{registerErrors.email}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              name="password"
              value={registerData.password}
              onChange={handleChange}
              className={registerErrors.password ? 'error' : ''}
              placeholder="•••••••"
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
              onChange={handleChange}
              className={registerErrors.confirm_password ? 'error' : ''}
              placeholder="•••••••"
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
            {loading ? 'Inscription...' : 'Créer mon compte'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Vous avez déjà un compte ?{' '}
            <Link to="/login" className="auth-link">
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
