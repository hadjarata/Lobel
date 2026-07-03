import React from 'react';
import './ErrorFallback.css';

const ErrorFallback = ({ error, onReset }) => {
  return (
    <div className="error-fallback">
      <div className="error-fallback-card">
        <p className="error-fallback-eyebrow">Lobel Store</p>
        <h1>Oups, une erreur est survenue</h1>
        <p className="error-fallback-text">
          L&apos;application a rencontré un problème inattendu. Vous pouvez réessayer ou
          retourner à l&apos;accueil.
        </p>

        {import.meta.env.DEV && error?.message && (
          <pre className="error-fallback-details">{error.message}</pre>
        )}

        <div className="error-fallback-actions">
          <button type="button" className="error-fallback-btn error-fallback-btn-primary" onClick={onReset}>
            Réessayer
          </button>
          <a href="/" className="error-fallback-btn error-fallback-btn-outline">
            Retour à l&apos;accueil
          </a>
        </div>
      </div>
    </div>
  );
};

export default ErrorFallback;
