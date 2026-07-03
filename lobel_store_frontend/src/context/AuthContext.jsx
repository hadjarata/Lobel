import React, { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login as loginService, register as registerService, getCurrentUser } from '../api/auth';
import { syncGuestCartToServer } from '../api/cart';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

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

  const login = useCallback(async (credentials) => {
    setLoading(true);
    try {
      const data = await loginService(credentials);

      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);

      const userData = await getCurrentUser();
      setUser(userData);
      setIsAuthenticated(true);

      await syncGuestCartToServer();

      const redirectTo = location.state?.from?.pathname || '/';
      navigate(redirectTo, { replace: true });

      return data;
    } finally {
      setLoading(false);
    }
  }, [navigate, location.state]);

  const register = useCallback(async (userData) => {
    setLoading(true);
    try {
      const data = await registerService(userData);

      navigate('/login', {
        state: {
          message: data.detail || 'Votre compte a été créé. Vérifiez votre email pour activer le compte.',
        },
        replace: true,
      });

      return data;
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);
    window.dispatchEvent(new Event('cartUpdated'));
  }, []);

  const requireAuth = useCallback((callback = null, options = {}) => {
    if (!isAuthenticated) {
      navigate('/login', {
        state: {
          from: options.from || {
            pathname: location.pathname,
            search: location.search,
          },
          message: options.message || 'Veuillez vous connecter pour continuer',
        },
      });
      return false;
    }

    if (callback && typeof callback === 'function') {
      callback();
    }

    return true;
  }, [isAuthenticated, navigate, location]);

  const value = useMemo(() => ({
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated,
    requireAuth,
  }), [user, loading, isAuthenticated, login, register, logout, requireAuth]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
