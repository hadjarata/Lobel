import api from "../api/axios";
import { ENDPOINTS } from "../api/endpoints";

export const login = async (credentials) => {
  try {
    const response = await api.post(ENDPOINTS.LOGIN, credentials);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await api.post(ENDPOINTS.CUSTOMERS, userData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const refreshToken = async (refresh) => {
  try {
    const response = await api.post(ENDPOINTS.REFRESH_TOKEN, { refresh });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const logout = async () => {
  try {
    const response = await api.post(ENDPOINTS.LOGOUT);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get(ENDPOINTS.CURRENT_USER);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const updateProfile = async (userData) => {
  try {
    const response = await api.put(ENDPOINTS.CURRENT_USER, userData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const changePassword = async (passwordData) => {
  try {
    const response = await api.post(ENDPOINTS.CHANGE_PASSWORD, passwordData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

// Validation des formulaires
export const validateLogin = (credentials) => {
  const errors = {};
  
  if (!credentials.email) {
    errors.email = 'L\'email est requis';
  } else if (!/\S+@\S+\.\S+/.test(credentials.email)) {
    errors.email = 'L\'email n\'est pas valide';
  }
  
  if (!credentials.password) {
    errors.password = 'Le mot de passe est requis';
  } else if (credentials.password.length < 6) {
    errors.password = 'Le mot de passe doit contenir au moins 6 caractères';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateRegister = (userData) => {
  const errors = {};
  
  if (!userData.first_name) {
    errors.first_name = 'Le nom est requis';
  }
  
  if (!userData.last_name) {
    errors.last_name = 'Le prénom est requis';
  }
  
  if (!userData.email) {
    errors.email = 'L\'email est requis';
  } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
    errors.email = 'L\'email n\'est pas valide';
  }
  
  if (!userData.password) {
    errors.password = 'Le mot de passe est requis';
  } else if (userData.password.length < 8) {
    errors.password = 'Le mot de passe doit contenir au moins 8 caractères';
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(userData.password)) {
    errors.password = 'Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre';
  }
  
  if (!userData.confirm_password) {
    errors.confirm_password = 'La confirmation du mot de passe est requise';
  } else if (userData.password !== userData.confirm_password) {
    errors.confirm_password = 'Les mots de passe ne correspondent pas';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};