import api from './axios';
import { ENDPOINTS } from './endpoints';
import {
  requestEmailVerification,
  requestLogin,
  requestPasswordReset,
  requestPasswordResetConfirmation,
  requestRegister,
} from '../auth/authApi';
import { AUTH_ERROR_CODES, normalizeAuthError } from '../auth/authErrors';
import { establishSession } from '../auth/authSession';
import { adaptCustomer } from './contracts/customer';

export const login = async (credentials) => {
  try {
    const tokens = await requestLogin(credentials);
    establishSession(tokens);
    return tokens;
  } catch (error) {
    throw normalizeAuthError(error, AUTH_ERROR_CODES.INVALID_CREDENTIALS);
  }
};

export const register = async (userData) => {
  try {
    return await requestRegister({
      email: userData.email,
      password: userData.password,
      first_name: userData.first_name,
      last_name: userData.last_name,
      country: userData.country,
      phone_number: userData.phone_number,
    });
  } catch (error) {
    throw normalizeAuthError(error, AUTH_ERROR_CODES.VALIDATION);
  }
};

export const getCurrentUser = (config = {}) => (
  api.get(ENDPOINTS.CURRENT_USER, config).then(({ data }) => adaptCustomer(data))
);

export const updateProfile = (customerId, userData) => (
  api.patch(ENDPOINTS.CUSTOMER_DETAIL(customerId), userData).then(({ data }) => adaptCustomer(data))
);

export const changePassword = (passwordData) => (
  api.post(ENDPOINTS.CHANGE_PASSWORD, passwordData).then(({ data }) => data)
);

export const requestPasswordResetEmail = async (payload, config = {}) => {
  try {
    return await requestPasswordReset(payload, config);
  } catch (error) {
    throw normalizeAuthError(error, AUTH_ERROR_CODES.VALIDATION);
  }
};

export const resetPassword = async (payload, config = {}) => {
  try {
    return await requestPasswordResetConfirmation(payload, config);
  } catch (error) {
    throw normalizeAuthError(error, AUTH_ERROR_CODES.VALIDATION);
  }
};

export const verifyEmail = async (payload, config = {}) => {
  try {
    return await requestEmailVerification(payload, config);
  } catch (error) {
    throw normalizeAuthError(error, AUTH_ERROR_CODES.VALIDATION);
  }
};

export const validatePassword = (password, confirmation) => {
  const errors = {};
  if (!password) errors.password = 'Le mot de passe est requis';
  else if (password.length < 10) errors.password = 'Le mot de passe doit contenir au moins 10 caractères';
  if (!confirmation) errors.confirm_password = 'La confirmation est requise';
  else if (password !== confirmation) errors.confirm_password = 'Les mots de passe ne correspondent pas';
  return { isValid: Object.keys(errors).length === 0, errors };
};

export const validateResetPassword = ({ password, confirm_password: confirmation }) => (
  validatePassword(password, confirmation)
);

export const validateLogin = ({ email, password }) => {
  const errors = {};
  if (!email) errors.email = "L'email est requis";
  else if (!/\S+@\S+\.\S+/.test(email)) errors.email = 'Email invalide';
  if (!password) errors.password = 'Mot de passe requis';
  return { isValid: Object.keys(errors).length === 0, errors };
};

export const validateEmailOnly = (email) => {
  const errors = {};
  if (!email) errors.email = "L'email est requis";
  else if (!/\S+@\S+\.\S+/.test(email)) errors.email = 'Email invalide';
  return { isValid: Object.keys(errors).length === 0, errors };
};

export const validateRegister = (data) => {
  const errors = {};
  if (!data.first_name || data.first_name.length < 2) errors.first_name = 'Le prénom doit contenir au moins 2 caractères';
  if (!data.last_name || data.last_name.length < 2) errors.last_name = 'Le nom doit contenir au moins 2 caractères';
  Object.assign(errors, validateEmailOnly(data.email).errors);
  if (!data.country) errors.country = 'Le pays est requis';
  if (data.phone_number && !/^\+?[0-9]{7,20}$/.test(data.phone_number.trim().replace(/\s+/g, ''))) {
    errors.phone_number = 'Numéro de téléphone invalide';
  }
  Object.assign(errors, validatePassword(data.password, data.confirm_password).errors);
  return { isValid: Object.keys(errors).length === 0, errors };
};
