import React from 'react';
import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useCart } from '../../cart/cartState';
import { useAuth } from '../../context/authState';
import Cart from './Cart';

vi.mock('../../cart/cartState', () => ({ useCart: vi.fn() }));
vi.mock('../../context/authState', () => ({ useAuth: vi.fn() }));

const line = {
  id: 21,
  variant_id: 7,
  product_name: 'Robe noire',
  variant_name: 'Noir · M',
  sku: 'RN-M',
  quantity: 2,
  unit_price: '15000.00',
  line_total: '30000.00',
  currency: 'XOF',
  image: '/robe.jpg',
  invalid: false,
};

const cartState = (overrides = {}) => ({
  status: 'ready',
  cart: { cart_total: '30000.00', currency: 'XOF' },
  lines: [line],
  itemCount: 2,
  isGuest: false,
  error: null,
  lineErrors: {},
  pendingLines: [],
  mergeReport: null,
  updateItemQuantity: vi.fn().mockResolvedValue(undefined),
  removeItem: vi.fn().mockResolvedValue(undefined),
  reloadCart: vi.fn(),
  ...overrides,
});

const renderCart = () => render(<MemoryRouter><Cart /></MemoryRouter>);

describe('Page Panier', () => {
  afterEach(cleanup);

  beforeEach(() => {
    useAuth.mockReturnValue({ isAuthenticated: true });
    useCart.mockReturnValue(cartState());
  });

  it('soigne le cas du panier vide', () => {
    useCart.mockReturnValue(cartState({
      cart: { cart_total: '0.00', currency: 'XOF' },
      lines: [],
      itemCount: 0,
    }));

    renderCart();

    expect(screen.getByRole('heading', { level: 1, name: 'Votre panier' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Votre panier est vide' })).toBeVisible();
    expect(screen.getByRole('link', { name: 'Découvrir la boutique' })).toHaveAttribute('href', '/shop');
  });

  it('modifie la quantité avec les contrôles existants', async () => {
    const state = cartState();
    useCart.mockReturnValue(state);
    renderCart();

    fireEvent.click(screen.getByRole('button', { name: 'Augmenter la quantité' }));
    await waitFor(() => expect(state.updateItemQuantity).toHaveBeenCalledWith(line, 3));

    fireEvent.click(screen.getByRole('button', { name: 'Diminuer la quantité' }));
    await waitFor(() => expect(state.updateItemQuantity).toHaveBeenCalledWith(line, 1));
  });

  it('supprime un article via la mutation du panier', async () => {
    const state = cartState();
    useCart.mockReturnValue(state);
    renderCart();

    fireEvent.click(screen.getByRole('button', { name: 'Retirer Robe noire' }));
    await waitFor(() => expect(state.removeItem).toHaveBeenCalledWith(line));
  });

  it('affiche les totaux serveur sans les recalculer', () => {
    renderCart();

    expect(screen.getByText('Sous-total')).toBeVisible();
    expect(screen.getAllByText('30000.00 XOF')).toHaveLength(3);
    expect(screen.getByText('Calculée au paiement')).toBeVisible();
    expect(screen.getByRole('button', { name: /Passer au paiement/i })).toBeEnabled();
  });
});
