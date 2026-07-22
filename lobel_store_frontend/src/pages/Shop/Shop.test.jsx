import React from 'react';
import {
  cleanup, fireEvent, render, screen, waitFor, within,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getCatalogFilterOptions } from '../../api/products';
import { useCatalogProducts } from '../../catalog/useCatalogProducts';
import Shop from './Shop';

vi.mock('../../api/products', () => ({
  getCatalogFilterOptions: vi.fn(),
}));

vi.mock('../../catalog/useCatalogProducts', () => ({
  useCatalogProducts: vi.fn(),
}));

vi.mock('../../components/product/ProductGrid', () => ({
  default: ({ products, loading }) => (
    <div data-testid="product-grid">
      {loading ? 'Chargement de la grille' : products.map(({ name }) => name).join(', ')}
    </div>
  ),
}));

const options = {
  categories: [{ id: 1, name: 'Robes' }],
  collections: [{ slug: 'soir', name: 'Soirée' }],
  colors: [{ id: 2, name: 'Noir', hex_code: '#111111' }],
  sizes: [{ id: 3, name: 'M' }],
  price: { min: 5000, max: 50000 },
};

const renderShop = (entry = '/shop') => render(
  <MemoryRouter initialEntries={[entry]}>
    <Shop />
  </MemoryRouter>,
);

describe('Boutique', () => {
  afterEach(() => cleanup());

  beforeEach(() => {
    window.innerWidth = 1024;
    getCatalogFilterOptions.mockResolvedValue(options);
    useCatalogProducts.mockReturnValue({
      products: [{ id: 10, name: 'Robe noire' }],
      count: 1,
      loading: false,
      error: null,
    });
  });

  it('affiche le nouvel en-tête et supprime complètement le tri', async () => {
    renderShop();

    expect(screen.getByRole('heading', { level: 1, name: 'Boutique' })).toBeVisible();
    expect(screen.getByRole('search')).toBeVisible();
    expect(screen.queryByText(/Trier par/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    expect(screen.getByText('1 produit')).toBeVisible();
    expect(screen.getByTestId('product-grid')).toHaveTextContent('Robe noire');
    await waitFor(() => expect(getCatalogFilterOptions).toHaveBeenCalled());
  });

  it('conserve les filtres utiles dans le panneau desktop', async () => {
    renderShop('/shop?collection=soir');

    expect(await screen.findByRole('heading', { level: 1, name: 'Soirée' })).toBeVisible();
    expect(screen.getByRole('heading', { name: 'Filtres' })).toBeVisible();
    expect(screen.getByText('Collections')).toBeVisible();
    expect(screen.getByText('Catégories')).toBeVisible();
    expect(screen.getByText('Prix')).toBeVisible();
    expect(screen.getByText('Tailles')).toBeVisible();
    expect(screen.getByText('Couleurs')).toBeVisible();
    expect(screen.getByText('Disponibilité')).toBeVisible();
  });

  it('ouvre et ferme le panneau de filtres sur mobile', async () => {
    window.innerWidth = 375;
    renderShop();

    const openButton = screen.getByRole('button', { name: /^Filtres/ });
    fireEvent.click(openButton);
    const dialog = await screen.findByRole('dialog', { name: 'Filtres du catalogue' });
    expect(dialog).toBeVisible();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Fermer les filtres' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });
});
