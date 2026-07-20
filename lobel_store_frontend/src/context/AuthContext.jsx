import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  changePassword as changePasswordService,
  getCurrentUser,
  login as loginService,
  register as registerService,
} from '../api/auth';
import { requestLogout } from '../auth/authApi';
import { AUTH_STATUS } from '../auth/authConstants';
import {
  clearSession,
  getRefreshToken,
  hasSession,
  isAccessTokenUsable,
  refreshSession as refreshSessionService,
  subscribeToSession,
} from '../auth/authSession';
import { normalizeAuthError } from '../auth/authErrors';
import { getSafeInternalRedirect } from '../auth/authRedirect';
import { syncGuestCartToServer } from '../api/cart';
import { AuthContext } from './authState';

export const AuthProvider = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const mounted = useRef(true);
  const logoutPromise = useRef(null);
  const operationLock = useRef(false);
  const [status, setStatus] = useState(AUTH_STATUS.INITIALIZING);
  const [user, setUser] = useState(null);
  const [operationPending, setOperationPending] = useState(false);

  const becomeAnonymous = useCallback(() => {
    if (!mounted.current) return;
    setUser(null);
    setStatus(AUTH_STATUS.ANONYMOUS);
  }, []);

  const reloadUser = useCallback(async (config = {}) => {
    const profile = await getCurrentUser(config);
    if (mounted.current) {
      setUser(profile);
      setStatus(AUTH_STATUS.AUTHENTICATED);
    }
    return profile;
  }, []);

  const refreshSession = useCallback(async () => {
    await refreshSessionService();
    return reloadUser();
  }, [reloadUser]);

  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    const restore = async () => {
      if (!hasSession()) {
        becomeAnonymous();
        return;
      }
      try {
        await refreshSessionService();
        await reloadUser({ signal: controller.signal });
      } catch (error) {
        if (error?.name !== 'CanceledError' && error?.name !== 'AbortError') {
          if (error?.status && [400, 401, 403].includes(error.status)) clearSession('expired');
          if (isAccessTokenUsable() && !error?.response) {
            setUser(null);
            setStatus(AUTH_STATUS.AUTHENTICATED);
          } else {
            becomeAnonymous();
          }
        }
      }
    };
    restore();
    const unsubscribe = subscribeToSession((reason) => {
      if (reason === 'expired' || reason === 'logout' || reason === 'password-changed') {
        becomeAnonymous();
      }
    });
    return () => {
      mounted.current = false;
      controller.abort();
      unsubscribe();
    };
  }, [becomeAnonymous, reloadUser]);

  const login = useCallback(async (credentials) => {
    if (operationLock.current) return null;
    operationLock.current = true;
    setOperationPending(true);
    clearSession('new-login');
    try {
      const tokens = await loginService(credentials);
      await reloadUser();
      try {
        await syncGuestCartToServer();
      } catch {
        // La synchronisation du panier ne doit pas invalider une connexion réussie.
      }
      const target = getSafeInternalRedirect(location.state?.from, '/');
      navigate(target, { replace: true });
      return tokens;
    } catch (error) {
      clearSession('login-failed');
      becomeAnonymous();
      throw normalizeAuthError(error);
    } finally {
      operationLock.current = false;
      if (mounted.current) setOperationPending(false);
    }
  }, [becomeAnonymous, location.state, navigate, reloadUser]);

  const register = useCallback(async (data) => {
    if (operationLock.current) return null;
    operationLock.current = true;
    setOperationPending(true);
    try {
      const result = await registerService(data);
      navigate('/login', {
        state: { message: result.detail || 'Compte créé. Vérifiez votre e-mail.' },
        replace: true,
      });
      return result;
    } finally {
      operationLock.current = false;
      if (mounted.current) setOperationPending(false);
    }
  }, [navigate]);

  const logout = useCallback(async () => {
    if (logoutPromise.current) return logoutPromise.current;
    const refresh = getRefreshToken();
    clearSession('logout');
    becomeAnonymous();
    window.dispatchEvent(new Event('cartUpdated'));
    logoutPromise.current = (refresh ? requestLogout(refresh) : Promise.resolve())
      .catch(() => undefined)
      .finally(() => {
        logoutPromise.current = null;
        navigate('/login', { replace: true, state: { message: 'Vous êtes déconnecté.' } });
      });
    return logoutPromise.current;
  }, [becomeAnonymous, navigate]);

  const changePassword = useCallback(async (payload) => {
    if (operationLock.current) return null;
    operationLock.current = true;
    setOperationPending(true);
    try {
      const result = await changePasswordService(payload);
      clearSession('password-changed');
      becomeAnonymous();
      navigate('/login', {
        replace: true,
        state: { message: 'Mot de passe modifié. Veuillez vous reconnecter.' },
      });
      return result;
    } catch (error) {
      throw normalizeAuthError(error);
    } finally {
      operationLock.current = false;
      if (mounted.current) setOperationPending(false);
    }
  }, [becomeAnonymous, navigate]);

  const requireAuth = useCallback((callback = null, options = {}) => {
    if (status !== AUTH_STATUS.AUTHENTICATED) {
      navigate('/login', {
        replace: true,
        state: {
          from: options.from || { pathname: location.pathname, search: location.search },
          message: options.message || 'Veuillez vous connecter pour continuer',
        },
      });
      return false;
    }
    callback?.();
    return true;
  }, [location.pathname, location.search, navigate, status]);

  const value = useMemo(() => ({
    status,
    user,
    isAuthenticated: status === AUTH_STATUS.AUTHENTICATED,
    loading: status === AUTH_STATUS.INITIALIZING || operationPending,
    operationPending,
    login,
    logout,
    register,
    refreshSession,
    reloadUser,
    changePassword,
    requireAuth,
  }), [status, user, operationPending, login, logout, register, refreshSession, reloadUser, changePassword, requireAuth]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
