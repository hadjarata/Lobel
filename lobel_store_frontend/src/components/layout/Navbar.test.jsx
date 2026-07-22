import React from 'react';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Navbar from './Navbar';

vi.mock('../../context/authState', () => ({
  useAuth: () => ({ isAuthenticated: true, logout: vi.fn() }),
}));

vi.mock('../../cart/cartState', () => ({
  useCart: () => ({ itemCount: 2 }),
}));

const renderAt = (path) => render(
  <MemoryRouter initialEntries={[path]}>
    <Navbar />
  </MemoryRouter>,
);

describe('Navbar', () => {
  afterEach(cleanup);

  it.each([
    ['/', 'Accueil'],
    ['/shop', 'Boutique'],
    ['/shop/nouveautes', 'Boutique'],
    ['/cart', 'Panier'],
    ['/cart/verification', 'Panier'],
    ['/profile', 'Profil'],
    ['/profile/settings', 'Profil'],
  ])('indique %s avec le lien %s actif', (path, label) => {
    renderAt(path);

    const activeLink = screen.getByRole('link', { name: new RegExp(label, 'i') });
    expect(activeLink).toHaveClass('nav-item-active');
    expect(activeLink).toHaveAttribute('aria-current', 'page');
  });

  it('ne garde pas Accueil actif sur les autres routes', () => {
    renderAt('/shop');

    expect(screen.getByRole('link', { name: /Accueil/i })).not.toHaveClass('nav-item-active');
  });

  it('conserve des zones tactiles identiques dans la navigation responsive', () => {
    renderAt('/cart');

    expect(screen.getByRole('navigation').querySelectorAll('.nav-item')).toHaveLength(5);
    expect(screen.getByRole('link', { name: /Panier/i })).toHaveTextContent('2');
  });
});
