import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { verifyEmail } from '../../api/auth';
import './Auth.css';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const uid = searchParams.get('uid');
  const token = searchParams.get('token');

  useEffect(() => {
    const runVerification = async () => {
      if (!uid || !token) {
        setError('Le lien de vérification est invalide ou incomplet.');
        return;
      }

      try {
        setLoading(true);
        const data = await verifyEmail({ uid, token });
        setMessage(data.detail || 'Email vérifié avec succès. Vous pouvez vous connecter.');
      } catch (err) {
        setError(err.response?.data?.detail || err.message || 'Impossible de vérifier votre adresse email.');
      } finally {
        setLoading(false);
      }
    };

    runVerification();
  }, [uid, token]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <h2>Lobel Store</h2>
        </div>
        <div className="auth-header">
          <h1>Vérification de l'email</h1>
          <p>Votre adresse email est en cours de vérification.</p>
        </div>

        <div className="auth-form">
          {loading && <div className="auth-info">Vérification en cours…</div>}
          {message && <div className="auth-success">{message}</div>}
          {error && <div className="auth-error">{error}</div>}
        </div>

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

export default VerifyEmail;
