import React from 'react';
import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchCart } from '../../api/cart';
import { getOrders } from '../../api/orders';
import { getPayments } from '../../api/payments';
import { getCustomerProfile, updateCustomerProfile } from '../../api/profile';
import { ApiValidationError } from '../../utils/apiErrors';
import Profile from './Profile';

vi.mock('../../api/cart', () => ({ fetchCart: vi.fn() }));
vi.mock('../../api/orders', () => ({ getOrders: vi.fn() }));
vi.mock('../../api/payments', () => ({ getPayments: vi.fn() }));
vi.mock('../../api/profile', () => ({
  getCustomerProfile: vi.fn(),
  updateCustomerProfile: vi.fn(),
}));

const customer = {
  id: 5,
  user: {
    id: 8,
    username: 'awa',
    first_name: 'Awa',
    last_name: 'Traoré',
    email: 'awa@example.com',
    is_active: true,
  },
  country: 'ML',
  phone_number: '+22370123456',
  address: 'Bamako, Mali',
  date_created: '2025-01-10T10:00:00Z',
};

const renderProfile = () => render(
  <MemoryRouter initialEntries={['/profile']}>
    <Profile />
  </MemoryRouter>,
);

describe('Page Profil', () => {
  afterEach(cleanup);

  beforeEach(() => {
    Element.prototype.scrollIntoView = vi.fn();
    getCustomerProfile.mockResolvedValue(customer);
    getOrders.mockResolvedValue({ results: [] });
    getPayments.mockResolvedValue({ results: [] });
    fetchCart.mockResolvedValue({ cart_items: 0, items: [] });
    updateCustomerProfile.mockResolvedValue(customer);
  });

  it('affiche un état de chargement puis le profil structuré', async () => {
    let resolveProfile;
    getCustomerProfile.mockReturnValue(new Promise((resolve) => { resolveProfile = resolve; }));
    renderProfile();

    expect(screen.getByText(/Chargement de votre espace client/i)).toBeVisible();
    resolveProfile(customer);

    expect(await screen.findByRole('heading', { level: 1, name: 'Mon profil' })).toBeVisible();
    await waitFor(() => expect(screen.getByRole('heading', { name: 'Identité' })).toBeVisible());
    expect(screen.getByRole('heading', { name: 'Coordonnées' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Adresse' })).toBeVisible();
  });

  it('affiche une erreur de récupération et permet de réessayer', async () => {
    getCustomerProfile.mockRejectedValueOnce(new Error('offline'));
    renderProfile();

    expect(await screen.findByText('Impossible de charger votre profil.')).toBeVisible();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeEnabled();
  });

  it('modifie et enregistre les informations existantes', async () => {
    const updated = {
      ...customer,
      user: { ...customer.user, first_name: 'Mariam' },
    };
    updateCustomerProfile.mockResolvedValue(updated);
    renderProfile();

    fireEvent.click(await screen.findByRole('button', { name: 'Modifier' }));
    const firstName = screen.getByLabelText('Prénom');
    fireEvent.change(firstName, { target: { value: 'Mariam' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer les modifications' }));

    await waitFor(() => expect(updateCustomerProfile).toHaveBeenCalledWith(5, {
      first_name: 'Mariam',
      last_name: 'Traoré',
      country: 'ML',
      phone_number: '+22370123456',
      address: 'Bamako, Mali',
    }));
    await waitFor(() => expect(screen.getAllByText('Mariam Traoré')).toHaveLength(2));
  });

  it('conserve la saisie et rapproche une erreur de validation du champ', async () => {
    updateCustomerProfile.mockRejectedValue(new ApiValidationError(
      'Certaines informations sont invalides.',
      { first_name: 'Ce prénom est invalide.' },
    ));
    renderProfile();

    fireEvent.click(await screen.findByRole('button', { name: 'Modifier' }));
    const firstName = screen.getByLabelText('Prénom');
    fireEvent.change(firstName, { target: { value: 'Valeur conservée' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer les modifications' }));

    await waitFor(() => expect(screen.getByText('Ce prénom est invalide.')).toBeVisible());
    expect(firstName).toHaveValue('Valeur conservée');
    expect(screen.getByRole('button', { name: 'Enregistrer les modifications' })).toBeEnabled();
  });
});
