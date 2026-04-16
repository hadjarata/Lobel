import api from "../api/axios";
import { ENDPOINTS } from "../api/endpoints";

// ajouter un produit au panier (order item)
export const addOrderItem = async (data) => {
  const response = await api.post(ENDPOINTS.ORDER_ITEMS, data);
  return response.data;
};

// récupérer les items
export const getOrderItems = async () => {
  const response = await api.get(ENDPOINTS.ORDER_ITEMS);
  return response.data;
};

// supprimer un item
export const deleteOrderItem = async (id) => {
  const response = await api.delete(ENDPOINTS.ORDER_ITEM_DETAIL(id));
  return response.data;
};