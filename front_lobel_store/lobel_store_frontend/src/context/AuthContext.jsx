import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login as loginService, register as registerService, getCurrentUser } from '../api/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Vérification au chargement
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access');

      if (token) {
        try {
          const userData = await getCurrentUser();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          setUser(null);
          setIsAuthenticated(false);
        }
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  // LOGIN
  const login = useCallback(async (credentials) => {
    setLoading(true);
    try {
      const data = await loginService(credentials);

      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);

      const userData = await getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);

      navigate('/', { replace: true });

      return data;
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // REGISTER
  const register = useCallback(async (userData) => {
    setLoading(true);
    try {
      const data = await registerService(userData);

      if (data.access && data.refresh) {
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);

        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setIsAuthenticated(true);

        navigate('/', { replace: true });
      }

      return data;
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // LOGOUT
  const logout = useCallback(() => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);
  }, []);

  // PROTECTION ROUTES
  const requireAuth = useCallback((callback = null) => {
    if (!isAuthenticated) {
      navigate('/login', {
        state: {
          from: {
            pathname: location.pathname,
            search: location.search
          },
          message: 'Veuillez vous connecter pour continuer'
        }
      });
      return false;
    }

    if (callback && typeof callback === 'function') {
      callback();
    }

    return true;
  }, [isAuthenticated, navigate, location]);

  // 🔥 MEMO (clé du problème)
  const value = useMemo(() => ({
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated,
    requireAuth
  }), [user, loading, isAuthenticated, login, register, logout, requireAuth]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// HOOK PROPRE (sans logs inutiles)
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};