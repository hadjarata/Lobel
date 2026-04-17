import api from "./axios";

export const login = async (credentials) => {
  try {
    const response = await api.post('/api/token/', credentials);
    return response.data; // access + refresh

  } catch (error) {
    if (error.response) {
      const message = error.response.data?.detail;

      // Messages d'erreur Django JWT
      if (message === "No active account found with the given credentials") {
        throw new Error("Email ou mot de passe incorrect");
      }

      if (message === "This field may not be blank.") {
        throw new Error("Veuillez remplir tous les champs");
      }

      throw new Error(message || "Erreur de connexion");
    }

    throw new Error("Impossible de se connecter au serveur");
  }
};

export const register = async (userData) => {
  try {
    const response = await api.post('/api/users/customers/', userData);
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

export const refreshToken = async (refresh) => {
  try {
    const response = await api.post('/api/token/refresh/', { refresh });
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const logout = async () => {
  try {
    const response = await api.post('/api/logout/');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getCurrentUser = async () => {
  try {
    const response = await api.get('/api/users/me/');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const updateProfile = async (userData) => {
  try {
    const response = await api.put('/api/users/me/', userData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const changePassword = async (passwordData) => {
  try {
    const response = await api.post('/api/password/change/', passwordData);
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
