import api from "./axios";
import { ENDPOINTS } from "./endpoints";

// =========================
// LOGIN
// =========================
export const login = async (credentials) => {
  console.log('api/auth.login() appelé avec:', credentials);
  try {
    const payload = {
      username: credentials.email, // Utiliser uniquement l'email
      password: credentials.password
    };
    console.log('Payload envoyé:', payload);
    console.log('Endpoint:', ENDPOINTS.LOGIN);
    
    const response = await api.post(ENDPOINTS.LOGIN, payload);
    console.log('Réponse API:', response.data);

    return response.data;

  } catch (error) {
    console.log('Erreur API login:', error);
    if (error.response) {
      const message = error.response.data?.detail;
      console.log('Message erreur:', message);

      if (message === "No active account found with the given credentials") {
        throw new Error("Votre compte n'est pas activé. Vérifiez votre email pour activer votre compte.");
      }

      throw new Error(message || "Erreur de connexion");
    }

    throw new Error("Impossible de se connecter au serveur");
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
    };
    
    const response = await api.post(ENDPOINTS.REGISTER, registerPayload);
    return response.data;
  } catch (error) {
    if (error.response?.data) {
      const errors = error.response.data;
      if (typeof errors === 'object') {
        // Gérer les erreurs de validation Django
        const messages = Object.values(errors).flat();
        throw new Error(messages[0] || "Erreur d'inscription");
      }
    }
    throw error;
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
    // ⚠️ optionnel : certains backends n'ont pas logout
  }
};

// =========================
// USER
// =========================
export const getCurrentUser = async () => {
  const response = await api.get(ENDPOINTS.CURRENT_USER);
  return response.data;
};

export const updateProfile = async (userData) => {
  const response = await api.put(ENDPOINTS.CURRENT_USER, userData);
  return response.data;
};

// =========================
// PASSWORD
// =========================
export const changePassword = async (passwordData) => {
  const response = await api.post(ENDPOINTS.CHANGE_PASSWORD, passwordData);
  return response.data;
};

export const requestPasswordReset = async (payload) => {
  const response = await api.post(ENDPOINTS.PASSWORD_RESET_REQUEST, payload);
  return response.data;
};

export const resetPassword = async (payload) => {
  const response = await api.post(ENDPOINTS.PASSWORD_RESET_CONFIRM, payload);
  return response.data;
};

export const verifyEmail = async (payload) => {
  const response = await api.post(ENDPOINTS.VERIFY_EMAIL, payload);
  return response.data;
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

  // =========================
  // FIRST NAME
  // =========================
  if (!userData.first_name) {
    errors.first_name = "Le prénom est requis";
  } else if (userData.first_name.length < 2) {
    errors.first_name = "Le prénom doit contenir au moins 2 caractères";
  }

  // =========================
  // LAST NAME
  // =========================
  if (!userData.last_name) {
    errors.last_name = "Le nom est requis";
  } else if (userData.last_name.length < 2) {
    errors.last_name = "Le nom doit contenir au moins 2 caractères";
  }

  // =========================
  // EMAIL
  // =========================
  if (!userData.email) {
    errors.email = "L'email est requis";
  } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
    errors.email = "Email invalide";
  }

  // =========================
  // PASSWORD
  // =========================
  if (!userData.password) {
    errors.password = "Le mot de passe est requis";
  } else if (userData.password.length < 6) {
    errors.password = "Le mot de passe doit contenir au moins 6 caractères";
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};