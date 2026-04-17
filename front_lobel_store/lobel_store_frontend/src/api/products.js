import api from "./axios";
import { ENDPOINTS } from './endpoints';

// récupérer tous les produits
export const getProducts = async () => {
  const response = await api.get(ENDPOINTS.PRODUCTS);
  return response.data;
};

// récupérer un produit
export const getProductById = async (id) => {
  const response = await api.get(ENDPOINTS.PRODUCT_DETAIL(id));
  return response.data;
};

// récupérer les best sellers (produits les plus vendus) - filtrage côté client
export const getBestSellers = async (limit = 4) => {
  const response = await api.get(`${ENDPOINTS.PRODUCTS}?limit=${limit}`);
  // Filtrer côté client pour les best sellers (sales_count > 0)
  const allProducts = response.data.results || response.data;
  const bestSellers = allProducts
    .filter(product => product.sales_count > 0)
    .sort((a, b) => b.sales_count - a.sales_count)
    .slice(0, limit);
  return bestSellers;
};

// récupérer les nouveautés via endpoint automatique
export const getNewProducts = async () => {
  try {
    const response = await api.get(ENDPOINTS.NEW_PRODUCTS);

    // gérer les deux formats possibles
    const products = response.data.results || response.data;

    if (!Array.isArray(products)) {
      console.warn("API response is not an array:", products);
      return [];
    }

    return products; // retourner tous les produits
  } catch (error) {
    console.error("Error in getNewProducts:", error);
    throw error;
  }
};

// récupérer les catégories
export const getCategories = async () => {
  const response = await api.get(ENDPOINTS.CATEGORIES);
  return response.data;
};

// récupérer les produits par catégorie
export const getProductsByCategory = async (categoryId) => {
  const response = await api.get(ENDPOINTS.CATEGORY_PRODUCTS(categoryId));
  return response.data;
};

// récupérer les collections
export const getCollections = async () => {
  const response = await api.get(ENDPOINTS.COLLECTIONS);
  return response.data;
};

// récupérer les produits par collection
export const getProductsByCollection = async (collectionId) => {
  const response = await api.get(ENDPOINTS.COLLECTION_PRODUCTS(collectionId));
  return response.data;
};

// rechercher des produits
export const searchProducts = async (query) => {
  const response = await api.get(`${ENDPOINTS.PRODUCTS}?search=${query}`);
  return response.data;
};
