import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login as loginService, register as registerService } from '../services/authService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Vérifier l'authentification au chargement
  useEffect(() => {
    const initAuth = () => {
      try {
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');

        if (storedToken && storedUser) {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        // Nettoyer les données corrompues
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login
  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      const response = await loginService(credentials);
      
      if (response.token && response.user) {
        // Stocker les données
        localStorage.setItem('token', response.token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Mettre à jour l'état
        setToken(response.token);
        setUser(response.user);
        setIsAuthenticated(true);

        // Redirection intelligente
        const from = location.state?.from?.pathname || '/shop';
        navigate(from, { replace: true });
        
        return { success: true };
      } else {
        throw new Error('Réponse invalide du serveur');
      }
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erreur de connexion' 
      };
    } finally {
      setLoading(false);
    }
  }, [navigate, location]);

  // Register
  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      const response = await registerService(userData);
      
      if (response.token && response.user) {
        // Stocker les données
        localStorage.setItem('token', response.token);
        localStorage.setItem('user', JSON.stringify(response.user));
        
        // Mettre à jour l'état
        setToken(response.token);
        setUser(response.user);
        setIsAuthenticated(true);

        // Redirection après inscription
        navigate('/shop', { replace: true });
        
        return { success: true };
      } else {
        throw new Error('Réponse invalide du serveur');
      }
    } catch (error) {
      console.error('Register error:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erreur d\'inscription' 
      };
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  // Logout
  const logout = useCallback(() => {
    // Nettoyer localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Réinitialiser l'état
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    // Redirection vers login
    navigate('/login');
  }, [navigate]);

  // Vérifier si l'utilisateur est authentifié
  const checkAuth = useCallback(() => {
    return isAuthenticated && !!token;
  }, [isAuthenticated, token]);

  // Rediriger vers login si non authentifié
  const requireAuth = useCallback(() => {
    if (!isAuthenticated) {
      // Sauvegarder la page actuelle pour redirection après login
      navigate('/login', { 
        state: { from: location },
        replace: true 
      });
      return false;
    }
    return true;
  }, [isAuthenticated, navigate, location]);

  // Obtenir le token pour les requêtes API
  const getAuthToken = useCallback(() => {
    return token || localStorage.getItem('token');
  }, [token]);

  const value = {
    // État
    user,
    token,
    loading,
    isAuthenticated,
    
    // Actions
    login,
    register,
    logout,
    checkAuth,
    requireAuth,
    getAuthToken,
    
    // Utilitaires
    isLoading: loading,
    hasToken: !!token,
    currentUser: user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
