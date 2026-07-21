import React from 'react';
import {
  cleanup, fireEvent, render, screen,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  afterEach, beforeEach, describe, expect, it, vi,
} from 'vitest';
import {
  getBestSellers, getCollections, getNewProducts,
} from '../../api/products';
import CollectionsSection from './CollectionsSection';
import NewProductsSection from './NewProductsSection';
import ProductsSection from './ProductsSection';

vi.mock('../../api/products', () => ({
  getBestSellers: vi.fn(),
  getCollections: vi.fn(),
  getNewProducts: vi.fn(),
}));

vi.mock('../product/ProductCard', () => ({
  default: ({ name }) => <article data-testid="product-card">{name}</article>,
}));

vi.mock('../product/CollectionCard', () => ({
  default: ({ title, link }) => <a href={link}>{title}</a>,
}));

const products = Array.from({ length: 5 }, (_, index) => ({
  id: index + 1,
  name: `Produit ${index + 1}`,
  price: '10000',
  image: `/product-${index + 1}.jpg`,
  variants: [],
}));

beforeEach(() => {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    value: 1200,
  });
  getNewProducts.mockResolvedValue(products);
  getBestSellers.mockResolvedValue(products);
  getCollections.mockResolvedValue({
    results: [{
      id: 1,
      name: 'Épure',
      slug: 'epure',
      description: 'Collection Épure',
      image_url: '/epure.jpg',
      products: [{ id: 1 }],
    }],
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('Home catalog sections', () => {
  it('uses the Design System section and preserves new-product expansion', async () => {
    const { container } = render(<NewProductsSection />);

    expect(container.querySelector('.ds-section')).toBeInTheDocument();
    expect(await screen.findAllByTestId('product-card')).toHaveLength(4);

    const toggle = screen.getByRole('button', {
      name: 'Afficher tous les nouveaux produits',
    });
    fireEvent.click(toggle);

    expect(screen.getAllByTestId('product-card')).toHaveLength(5);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('button', { name: 'Réduire les nouveautés' }))
      .toBeInTheDocument();
  });

  it('preserves the collection route built from its slug', async () => {
    render(
      <MemoryRouter>
        <CollectionsSection />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('link', { name: 'Épure' }))
      .toHaveAttribute('href', '/shop?collection=epure');
  });

  it('keeps the best-seller limit at three products', async () => {
    render(
      <MemoryRouter>
        <ProductsSection />
      </MemoryRouter>,
    );

    expect(await screen.findAllByTestId('product-card')).toHaveLength(3);
    expect(screen.getByRole('heading', { name: 'Best Sellers' }))
      .toBeInTheDocument();
    expect(screen.getByText('Nos créations les plus convoitées'))
      .toBeInTheDocument();
    expect(getBestSellers).toHaveBeenCalledTimes(1);
  });

  it('keeps an actionable error state', async () => {
    getNewProducts.mockRejectedValueOnce(new Error('offline'));
    render(<NewProductsSection />);

    expect(await screen.findByText('Impossible de charger les nouveautés'))
      .toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeEnabled();
  });

  it('keeps the empty-state shop action', async () => {
    getNewProducts.mockResolvedValueOnce([]);
    render(<NewProductsSection />);

    expect(await screen.findByText('Aucune nouveauté disponible pour le moment'))
      .toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Voir la boutique' })).toBeEnabled();
  });
});
