import api from "./axios";
import { ENDPOINTS } from "./endpoints";
import { parseApiError, throwApiValidationError } from "../utils/apiErrors";

const LOGIN_INACTIVE_MESSAGE = "No active account found with the given credentials";

const translateLoginMessage = (message) => {
  if (message === LOGIN_INACTIVE_MESSAGE) {
    return "Votre compte n'est pas activé. Vérifiez votre email pour activer votre compte.";
  }

  return message || "Erreur de connexion";
};

// =========================
// LOGIN (JWT – /api/token/)
// =========================
export const login = async (credentials) => {
  try {
    const payload = {
      username: credentials.email,
      password: credentials.password,
    };

    const response = await api.post(ENDPOINTS.LOGIN, payload);
    return response.data;
  } catch (error) {
    if (error.response?.data?.detail) {
      throw new Error(translateLoginMessage(error.response.data.detail));
    }

    const parsed = parseApiError(error, "Impossible de se connecter au serveur");
    throw new Error(parsed.message);
  }
};

// =========================
// REGISTER
// =========================
export const register = async (userData) => {
  try {
    const registerPayload = {
      email: userData.email,
      password: userData.password,
      first_name: userData.first_name,
      last_name: userData.last_name,
      country: userData.country,
      phone_number: userData.phone_number,
    };

    const response = await api.post(ENDPOINTS.REGISTER, registerPayload);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, "Erreur d'inscription");
  }
};

// =========================
// REFRESH TOKEN
// =========================
export const refreshToken = async (refresh) => {
  const response = await api.post(ENDPOINTS.REFRESH_TOKEN, { refresh });
  return response.data;
};

// =========================
// LOGOUT
// =========================
export const logout = async () => {
  try {
    await api.post(ENDPOINTS.LOGOUT);
  } catch (error) {
    // optionnel : certains backends n'ont pas logout
  }
};

// =========================
// USER
// =========================
export const getCurrentUser = async () => {
  const response = await api.get(ENDPOINTS.CURRENT_USER);
  return response.data;
};

export const updateProfile = async (customerId, userData) => {
  try {
    const response = await api.patch(ENDPOINTS.CUSTOMER_DETAIL(customerId), userData);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, "Impossible de mettre à jour le profil.");
  }
};

// =========================
// PASSWORD
// =========================
export const changePassword = async (passwordData) => {
  const response = await api.post(ENDPOINTS.CHANGE_PASSWORD, passwordData);
  return response.data;
};

export const requestPasswordReset = async (payload) => {
  try {
    const response = await api.post(ENDPOINTS.PASSWORD_RESET_REQUEST, payload);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, "Impossible d'envoyer l'email de réinitialisation.");
  }
};

export const resetPassword = async (payload) => {
  try {
    const response = await api.post(ENDPOINTS.PASSWORD_RESET_CONFIRM, payload);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, "Impossible de réinitialiser le mot de passe.");
  }
};

export const verifyEmail = async (payload) => {
  try {
    const response = await api.post(ENDPOINTS.VERIFY_EMAIL, payload);
    return response.data;
  } catch (error) {
    throwApiValidationError(error, "Impossible de vérifier l'email.");
  }
};

export const validateResetPassword = (passwordData) => {
  const errors = {};

  if (!passwordData.password) {
    errors.password = "Le mot de passe est requis";
  } else if (passwordData.password.length < 6) {
    errors.password = "Le mot de passe doit contenir au moins 6 caractères";
  }

  if (!passwordData.confirm_password) {
    errors.confirm_password = "La confirmation est requise";
  } else if (passwordData.password !== passwordData.confirm_password) {
    errors.confirm_password = "Les mots de passe ne correspondent pas";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateLogin = (credentials) => {
  const errors = {};

  if (!credentials.email) {
    errors.email = "L'email est requis";
  } else if (!/\S+@\S+\.\S+/.test(credentials.email)) {
    errors.email = "Email invalide";
  }

  if (!credentials.password) {
    errors.password = "Mot de passe requis";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateEmailOnly = (email) => {
  const errors = {};

  if (!email) {
    errors.email = "L'email est requis";
  } else if (!/\S+@\S+\.\S+/.test(email)) {
    errors.email = "Email invalide";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateRegister = (userData) => {
  const errors = {};

  if (!userData.first_name) {
    errors.first_name = "Le prénom est requis";
  } else if (userData.first_name.length < 2) {
    errors.first_name = "Le prénom doit contenir au moins 2 caractères";
  }

  if (!userData.last_name) {
    errors.last_name = "Le nom est requis";
  } else if (userData.last_name.length < 2) {
    errors.last_name = "Le nom doit contenir au moins 2 caractères";
  }

  if (!userData.email) {
    errors.email = "L'email est requis";
  } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
    errors.email = "Email invalide";
  }

  if (!userData.country) {
    errors.country = "Le pays est requis";
  }

  if (userData.phone_number) {
    const normalizedPhone = userData.phone_number.trim().replace(/\s+/g, '');
    if (!/^\+?[0-9]{7,20}$/.test(normalizedPhone)) {
      errors.phone_number = 'Numéro de téléphone invalide';
    }
  }

  if (!userData.password) {
    errors.password = "Le mot de passe est requis";
  } else if (userData.password.length < 6) {
    errors.password = "Le mot de passe doit contenir au moins 6 caractères";
  }

  if (!userData.confirm_password) {
    errors.confirm_password = "La confirmation du mot de passe est requise";
  } else if (userData.password && userData.password !== userData.confirm_password) {
    errors.confirm_password = "Les mots de passe ne correspondent pas";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
