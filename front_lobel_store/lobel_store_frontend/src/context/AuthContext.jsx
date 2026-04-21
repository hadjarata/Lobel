import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login as loginService, register as registerService, getCurrentUser } from '../api/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Loading initial pour vérifier le token
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Vérifier si l'utilisateur est déjà connecté au chargement
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access');
      
      if (token) {
        try {
          const userData = await getCurrentUser();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          // Token invalide, nettoyer le localStorage
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

  const login = async (credentials) => {
    console.log('AuthContext.login() appelé avec:', credentials);
    setLoading(true);
    try {
      console.log('Appel de loginService...');
      const data = await loginService(credentials);
      console.log('loginService réponse:', data);

      // Stocker les tokens
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      console.log('Tokens stockés');

      // Récupérer les données utilisateur
      console.log('Récupération user data...');
      const userData = await getCurrentUser();
      console.log('User data reçue:', userData);
      setUser(userData);
      setIsAuthenticated(true);

      // Redirection vers la page d'accueil après login réussi
      navigate('/', { replace: true });

      return data;
    } catch (error) {
      console.log('Erreur dans AuthContext.login:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const data = await registerService(userData);

      // Si l'inscription renvoie des tokens (cas rare)
      if (data.access && data.refresh) {
        localStorage.setItem('access', data.access);
        localStorage.setItem('refresh', data.refresh);
        
        const currentUser = await getCurrentUser();
        setUser(currentUser);
        setIsAuthenticated(true);

        // Redirection vers la page d'accueil après register réussi
        navigate('/', { replace: true });
      }

      return data;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Nettoyer le localStorage
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    
    // Réinitialiser l'état
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);
  };

  // Fonction pour protéger les actions nécessitant une authentification
  const requireAuth = (callback = null) => {
    if (!isAuthenticated) {
      // Sauvegarder la page actuelle pour le retour après login
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
    
    // Si connecté et callback fourni, exécuter le callback
    if (callback && typeof callback === 'function') {
      callback();
    }
    
    return true;
  };

  return (
    <AuthContext.Provider value={{
      user,
      login,
      register,
      logout,
      loading,
      isAuthenticated,
      requireAuth
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  console.log('useAuth hook appelé');
  try {
    const context = useContext(AuthContext);
    console.log('useAuth context obtenu:', !!context);
    if (!context) {
      console.log('useAuth ERREUR: context non trouvé!');
      throw new Error('useAuth must be used within an AuthProvider');
    }
    console.log('useAuth retourné:', { 
      login: !!context.login, 
      loading: context.loading, 
      user: !!context.user,
      isAuthenticated: context.isAuthenticated 
    });
    return context;
  } catch (error) {
    console.log('useAuth ERREUR:', error);
    throw error;
  }
};
