import React from 'react';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CartProvider } from './CartContext';
import { useCart } from './cartState';
import { addGuestLine, readGuestCart } from './cartStorage';

const state = vi.hoisted(() => ({
  auth: { isAuthenticated: false, status: 'anonymous', user: null },
  api: {
    addServerCartItem: vi.fn(), clearServerCart: vi.fn(), fetchServerCart: vi.fn(),
    mergeGuestCart: vi.fn(), removeServerCartItem: vi.fn(), resolveVariants: vi.fn(),
    updateServerCartItem: vi.fn(),
  },
}));
vi.mock('../context/authState', () => ({ useAuth: () => state.auth }));
vi.mock('../api/cart', () => state.api);

const variant = {
  id: 7, product_id: 2, product_name: 'Robe', sku: 'R-7',
  color: { id: 1, name: 'Rose' }, size: { id: 2, name: 'M' },
  attributes: {}, price: '1250.50', stock: 5, is_available: true, image: null,
};
const emptyServer = {
  id: null, items: [], cart_total: '0.00', cart_items: 0,
  complete: false, status: 'cart', currency: 'XOF',
};

const Probe = () => {
  const cart = useCart();
  return <>
    <output data-testid="state">{JSON.stringify({
      status: cart.status, count: cart.itemCount, guest: cart.isGuest,
      lines: cart.lines.length, error: cart.error?.code || null,
    })}</output>
    <button onClick={() => cart.addItem(variant, 1)}>add</button>
    <button onClick={() => cart.lines[0] && cart.updateItemQuantity(cart.lines[0], 2)}>update</button>
    <button onClick={() => cart.lines[0] && cart.removeItem(cart.lines[0])}>remove</button>
    <button onClick={() => cart.clearCart()}>clear</button>
    <button onClick={() => cart.reloadCart()}>reload</button>
  </>;
};

const mount = () => render(<CartProvider><Probe /></CartProvider>);
const snapshot = () => JSON.parse(screen.getByTestId('state').textContent);
afterEach(cleanup);

describe('central cart lifecycle', () => {
  beforeEach(() => {
    localStorage.clear();
    state.auth = { isAuthenticated: false, status: 'anonymous', user: null };
    Object.values(state.api).forEach((mock) => mock.mockReset());
    state.api.resolveVariants.mockResolvedValue({ variants: [variant], missingIds: [] });
    state.api.fetchServerCart.mockResolvedValue(emptyServer);
    state.api.addServerCartItem.mockResolvedValue({});
    state.api.updateServerCartItem.mockResolvedValue({});
    state.api.removeServerCartItem.mockResolvedValue({});
    state.api.clearServerCart.mockResolvedValue(emptyServer);
  });

  it('loads an empty guest cart', async () => {
    mount();
    await waitFor(() => expect(snapshot()).toMatchObject({ status: 'ready', count: 0, guest: true }));
  });
  it('restores guest lines with one batch resolution', async () => {
    addGuestLine(7, 2);
    mount();
    await waitFor(() => expect(snapshot().count).toBe(2));
    expect(state.api.resolveVariants).toHaveBeenCalledWith([7], expect.any(Object));
  });
  it('adds a guest variant and updates the central count', async () => {
    mount();
    await waitFor(() => expect(snapshot().status).toBe('ready'));
    fireEvent.click(screen.getByText('add'));
    await waitFor(() => expect(snapshot().count).toBe(1));
    expect(readGuestCart().items[0]).toMatchObject({ variant_id: 7, quantity: 1 });
  });
  it('updates a guest quantity', async () => {
    addGuestLine(7, 1);
    mount();
    await waitFor(() => expect(snapshot().count).toBe(1));
    fireEvent.click(screen.getByText('update'));
    await waitFor(() => expect(snapshot().count).toBe(2));
  });
  it('removes a guest line', async () => {
    addGuestLine(7, 1);
    mount();
    await waitFor(() => expect(snapshot().count).toBe(1));
    fireEvent.click(screen.getByText('remove'));
    await waitFor(() => expect(snapshot().count).toBe(0));
  });
  it('loads only the server cart when authenticated', async () => {
    state.auth = { isAuthenticated: true, status: 'authenticated', user: { id: 1 } };
    state.api.fetchServerCart.mockResolvedValue({ ...emptyServer, id: 1, cart_items: 3 });
    mount();
    await waitFor(() => expect(snapshot()).toMatchObject({ count: 3, guest: false }));
    expect(state.api.resolveVariants).not.toHaveBeenCalled();
  });
  it('uses a server mutation for authenticated add', async () => {
    state.auth = { isAuthenticated: true, status: 'authenticated', user: { id: 1 } };
    mount();
    await waitFor(() => expect(snapshot().status).toBe('ready'));
    fireEvent.click(screen.getByText('add'));
    await waitFor(() => expect(state.api.addServerCartItem).toHaveBeenCalledWith(7, 1));
  });
  it('prevents duplicate concurrent additions', async () => {
    state.auth = { isAuthenticated: true, status: 'authenticated', user: { id: 1 } };
    let release;
    state.api.addServerCartItem.mockReturnValue(new Promise((resolve) => { release = resolve; }));
    mount();
    await waitFor(() => expect(snapshot().status).toBe('ready'));
    fireEvent.click(screen.getByText('add'));
    fireEvent.click(screen.getByText('add'));
    expect(state.api.addServerCartItem).toHaveBeenCalledTimes(1);
    await act(async () => release({}));
  });
  it('preserves guest storage when merge fails', async () => {
    addGuestLine(7, 1);
    state.auth = { isAuthenticated: true, status: 'authenticated', user: { id: 1 } };
    state.api.mergeGuestCart.mockRejectedValue(new Error('network'));
    mount();
    await waitFor(() => expect(snapshot().status).toBe('error'));
    expect(readGuestCart().items).toHaveLength(1);
  });
  it('clears accepted guest lines only after merge confirmation', async () => {
    addGuestLine(7, 1);
    state.auth = { isAuthenticated: true, status: 'authenticated', user: { id: 1 } };
    state.api.mergeGuestCart.mockResolvedValue({
      cart: { ...emptyServer, id: 1, cart_items: 1 },
      merged_items: [{ variant_id: 7, accepted_quantity: 1 }],
      adjusted_items: [], rejected_items: [],
    });
    mount();
    await waitFor(() => expect(snapshot().count).toBe(1));
    expect(readGuestCart().items).toEqual([]);
  });
});
