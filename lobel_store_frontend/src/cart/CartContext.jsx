import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  addServerCartItem, clearServerCart, fetchServerCart, mergeGuestCart,
  removeServerCartItem, resolveVariants, updateServerCartItem,
} from '../api/cart';
import { useAuth } from '../context/authState';
import { CART_MAX_QUANTITY, CART_STATUS } from './cartConstants';
import { normalizeCartError } from './cartErrors';
import {
  addGuestLine, clearGuestCartStorage, ensureMergeKey, readGuestCart,
  removeGuestLine, updateGuestLine, writeGuestCart,
} from './cartStorage';
import { CartContext } from './cartState';

const emptyGuest = () => ({
  id: null, items: [], cart_total: null, cart_items: 0,
  complete: false, status: 'cart', isGuest: true, currency: 'XOF',
});

const hydrateGuest = async (signal) => {
  const stored = readGuestCart();
  if (!stored.items.length) return { cart: emptyGuest(), errors: {} };
  const resolved = await resolveVariants(stored.items.map((line) => line.variant_id), { signal });
  const byId = new Map(resolved.variants.map((variant) => [variant.id, variant]));
  const errors = {};
  const items = stored.items.map((line) => {
    const variant = byId.get(line.variant_id);
    if (!variant) {
      errors[line.variant_id] = { code: 'invalid_variant', message: 'Cette variante n’existe plus.' };
      return { id: `guest-${line.variant_id}`, ...line, invalid: true };
    }
    if (!variant.is_available || line.quantity > variant.stock) {
      errors[variant.id] = {
        code: variant.is_available ? 'insufficient_stock' : 'inactive_variant',
        message: variant.is_available ? `Stock disponible : ${variant.stock}.` : 'Variante indisponible.',
      };
    }
    return {
      id: `guest-${variant.id}`, product_id: variant.product_id,
      product_name: variant.product_name, variant_id: variant.id,
      variant_name: [variant.color?.name, variant.size?.name].filter(Boolean).join(' / '),
      color: variant.color?.name || '', size: variant.size?.name || '',
      sku: variant.sku, quantity: line.quantity, unit_price: variant.price,
      line_total: null, currency: 'XOF', image: variant.image, variant,
      invalid: Boolean(errors[variant.id]),
    };
  });
  return {
    cart: { ...emptyGuest(), items, cart_items: items.reduce((sum, item) => sum + item.quantity, 0) },
    errors,
  };
};

export const CartProvider = ({ children }) => {
  const { isAuthenticated, status: authStatus, user } = useAuth();
  const [status, setStatus] = useState(CART_STATUS.IDLE);
  const [cart, setCart] = useState(emptyGuest);
  const [error, setError] = useState(null);
  const [lineErrors, setLineErrors] = useState({});
  const [pendingLines, setPendingLines] = useState([]);
  const [mergeReport, setMergeReport] = useState(null);
  const generation = useRef(0);
  const controller = useRef(null);
  const locks = useRef(new Set());

  const newRequest = () => {
    generation.current += 1;
    controller.current?.abort();
    controller.current = new AbortController();
    return { id: generation.current, signal: controller.current.signal };
  };

  const reloadCart = useCallback(async () => {
    const request = newRequest();
    setStatus(CART_STATUS.LOADING);
    try {
      const result = isAuthenticated
        ? { cart: await fetchServerCart({ signal: request.signal }), errors: {} }
        : await hydrateGuest(request.signal);
      if (request.id === generation.current) {
        setCart(result.cart); setLineErrors(result.errors); setError(null);
        setStatus(CART_STATUS.READY);
      }
      return result.cart;
    } catch (requestError) {
      const normalized = normalizeCartError(requestError);
      if (request.id === generation.current && !normalized.isCanceled) {
        setError(normalized); setStatus(CART_STATUS.ERROR);
      }
      return null;
    }
  }, [isAuthenticated]);

  const mergeStoredCart = useCallback(async () => {
    const stored = readGuestCart();
    if (!stored.items.length) return fetchServerCart();
    const keyed = ensureMergeKey();
    const response = await mergeGuestCart(keyed.items, keyed.pending_merge_key);
    const accepted = new Map([...response.merged_items, ...response.adjusted_items]
      .map((item) => [item.variant_id, item.accepted_quantity]));
    const remaining = keyed.items.flatMap((line) => {
      const quantity = line.quantity - (accepted.get(line.variant_id) || 0);
      return quantity > 0 ? [{ ...line, quantity }] : [];
    });
    if (remaining.length) writeGuestCart({ ...keyed, items: remaining, pending_merge_key: null });
    else clearGuestCartStorage();
    setMergeReport(response);
    return response.cart;
  }, []);

  useEffect(() => {
    if (authStatus === 'initializing') return undefined;
    if (isAuthenticated && !user?.id) return undefined;
    const request = newRequest();
    setStatus(CART_STATUS.LOADING);
    const promise = isAuthenticated ? mergeStoredCart().then((value) => ({ cart: value, errors: {} }))
      : hydrateGuest(request.signal);
    promise.then((result) => {
      if (request.id === generation.current) {
        setCart(result.cart); setLineErrors(result.errors); setError(null);
        setStatus(CART_STATUS.READY);
      }
    }).catch((requestError) => {
      const normalized = normalizeCartError(requestError);
      if (request.id === generation.current && !normalized.isCanceled) {
        setError(normalized); setStatus(CART_STATUS.ERROR);
      }
    });
    return () => controller.current?.abort();
  }, [authStatus, isAuthenticated, mergeStoredCart, user?.id]);

  const mutate = useCallback(async (key, operation) => {
    if (locks.current.has(key)) return null;
    const startedGeneration = generation.current;
    locks.current.add(key);
    setPendingLines((current) => [...current, key]);
    setStatus(CART_STATUS.MUTATING);
    try {
      const result = await operation();
      if (startedGeneration === generation.current) await reloadCart();
      return result;
    } catch (requestError) {
      const normalized = requestError?.code ? requestError : normalizeCartError(requestError);
      if (startedGeneration === generation.current) {
        setLineErrors((current) => ({ ...current, [key]: normalized }));
        setStatus(CART_STATUS.READY);
      }
      throw normalized;
    } finally {
      locks.current.delete(key);
      setPendingLines((current) => current.filter((item) => item !== key));
    }
  }, [reloadCart]);

  const addItem = useCallback((variant, quantity = 1) => {
    if (!variant?.id || !Number.isInteger(quantity) || quantity < 1 || quantity > CART_MAX_QUANTITY) {
      return Promise.reject({ code: 'invalid_quantity', message: 'Sélection ou quantité invalide.' });
    }
    const existingQuantity = cart.items.find(
      (item) => item.variant_id === variant.id,
    )?.quantity || 0;
    if (variant.is_available === false || variant.stock < existingQuantity + quantity) {
      return Promise.reject({ code: 'insufficient_stock', message: 'Stock insuffisant.' });
    }
    return mutate(`add-${variant.id}`, async () => {
      if (isAuthenticated) return addServerCartItem(variant.id, quantity);
      addGuestLine(variant.id, quantity);
      return null;
    });
  }, [cart.items, isAuthenticated, mutate]);

  const updateItemQuantity = useCallback((item, quantity) => mutate(item.id, async () => {
    if (!Number.isInteger(quantity) || quantity < 1 || quantity > CART_MAX_QUANTITY) {
      throw { code: 'invalid_quantity', message: 'Quantité invalide.' };
    }
    if (!isAuthenticated && item.variant?.stock != null && quantity > item.variant.stock) {
      throw { code: 'insufficient_stock', message: `Stock disponible : ${item.variant.stock}.` };
    }
    if (isAuthenticated) return updateServerCartItem(item.id, quantity);
    updateGuestLine(item.variant_id, quantity);
    return null;
  }), [isAuthenticated, mutate]);

  const removeItem = useCallback((item) => mutate(item.id, async () => {
    if (isAuthenticated) {
      try { await removeServerCartItem(item.id); } catch (requestError) {
        if (requestError?.response?.status !== 404) throw requestError;
      }
    } else removeGuestLine(item.variant_id);
  }), [isAuthenticated, mutate]);

  const clearCart = useCallback(() => mutate('clear', async () => {
    if (isAuthenticated) await clearServerCart(); else clearGuestCartStorage();
  }), [isAuthenticated, mutate]);

  const value = useMemo(() => ({
    status, cart, lines: cart.items || [], itemCount: cart.cart_items || 0,
    isGuest: !isAuthenticated, error, lineErrors, pendingLines, mergeReport,
    addItem, updateItemQuantity, removeItem, clearCart, reloadCart,
    mergeGuestCart: mergeStoredCart,
  }), [status, cart, isAuthenticated, error, lineErrors, pendingLines, mergeReport,
    addItem, updateItemQuantity, removeItem, clearCart, reloadCart, mergeStoredCart]);
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
