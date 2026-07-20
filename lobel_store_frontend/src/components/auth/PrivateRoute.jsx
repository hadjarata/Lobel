import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/authState';
import { AUTH_STATUS } from '../../auth/authConstants';

const PrivateRoute = ({ children }) => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === AUTH_STATUS.INITIALIZING) {
    return <div role="status" aria-live="polite">Chargement de votre session…</div>;
  }

  if (status === AUTH_STATUS.ANONYMOUS) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default PrivateRoute;
