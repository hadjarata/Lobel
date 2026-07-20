import { createContext, useContext } from 'react';
export const CartContext = createContext(null);
export const useCart = () => {
  const value = useContext(CartContext);
  if (!value) throw new Error('useCart must be used within CartProvider');
  return value;
};
