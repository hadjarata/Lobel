import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json"
  }
});

// 🔥 AJOUT AUTOMATIQUE DU TOKEN
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("Token envoyé:", token);
      console.log("Headers Authorization:", config.headers.Authorization);
    } else {
      console.log("Aucun token trouvé dans localStorage");
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;