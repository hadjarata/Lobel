import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import {
  afterEach, beforeEach, describe, expect, it, vi,
} from 'vitest';
import { getCustomDressService } from '../../api/homeContent';
import CustomDressSection from './CustomDressSection';

vi.mock('../../api/homeContent', () => ({
  getCustomDressService: vi.fn(),
}));

const service = {
  title: 'Une tenue conçue spécialement pour vous',
  description: 'Décrivez votre modèle.',
  imageUrl: 'https://cdn.example.test/dress.webp',
  whatsappPhone: '22370123456',
  whatsappMessage: 'Bonjour LobelStore, robe & tissu.',
  buttonLabel: 'Discuter sur WhatsApp',
  availabilityText: 'Service disponible du lundi au samedi',
  responseTimeText: 'Réponse habituelle sous 24 heures',
  pricingNotice: 'Le prix dépend du modèle et des matières.',
  steps: ['Inspiration', 'Tissu et mesures', 'Estimation', 'Validation'],
};

beforeEach(() => {
  getCustomDressService.mockResolvedValue(service);
  HTMLDialogElement.prototype.showModal = function showModal() {
    this.open = true;
  };
  HTMLDialogElement.prototype.close = function close() {
    this.open = false;
    this.dispatchEvent(new Event('close'));
  };
  window.requestAnimationFrame = (callback) => callback();
});

afterEach(cleanup);

describe('CustomDressSection', () => {
  it('loads and renders API content without authentication', async () => {
    render(<CustomDressSection />);
    expect(await screen.findByRole('heading', { name: service.title })).toBeVisible();
    expect(screen.getByText(service.availabilityText)).toBeVisible();
    expect(screen.getByText(service.responseTimeText)).toBeVisible();
    expect(document.querySelector('.custom-dress-media img')).toHaveAttribute('loading', 'lazy');
  });

  it('opens an accessible four-step dialog and focuses the final action', async () => {
    render(<CustomDressSection />);
    const opener = await screen.findByRole('button', { name: service.buttonLabel });
    fireEvent.click(opener);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('open');
    expect(screen.getAllByRole('listitem')).toHaveLength(4);
    expect(screen.getByRole('link', { name: 'Continuer sur WhatsApp' })).toHaveFocus();
  });

  it('builds only a fixed, encoded wa.me URL with safe new-tab attributes', async () => {
    render(<CustomDressSection />);
    fireEvent.click(await screen.findByRole('button', { name: service.buttonLabel }));
    const link = screen.getByRole('link', { name: 'Continuer sur WhatsApp' });
    expect(link).toHaveAttribute(
      'href',
      `https://wa.me/22370123456?text=${encodeURIComponent(service.whatsappMessage)}`,
    );
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(link.href).not.toMatch(/email|address|profile|user/i);
  });

  it('closes with Escape and restores focus', async () => {
    render(<CustomDressSection />);
    const opener = await screen.findByRole('button', { name: service.buttonLabel });
    fireEvent.click(opener);
    fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }));
    await waitFor(() => expect(opener).toHaveFocus());
  });

  it('keeps content when the image fails', async () => {
    render(<CustomDressSection />);
    await screen.findByRole('heading', { name: service.title });
    const image = document.querySelector('.custom-dress-media img');
    fireEvent.error(image);
    expect(screen.getByRole('heading', { name: service.title })).toBeVisible();
    expect(document.querySelector('.custom-dress-media img')).not.toBeInTheDocument();
  });

  it.each([
    ['no configuration', Promise.resolve(null)],
    ['API failure', () => Promise.reject(new Error('offline'))],
  ])('hides cleanly on %s', async (_name, result) => {
    getCustomDressService.mockReturnValueOnce(
      typeof result === 'function' ? result() : result,
    );
    const { container } = render(<CustomDressSection />);
    await waitFor(() => expect(container).toBeEmptyDOMElement());
  });

  it('ignores a late response after unmount', async () => {
    let resolve;
    getCustomDressService.mockReturnValueOnce(new Promise((done) => { resolve = done; }));
    const { unmount } = render(<CustomDressSection />);
    unmount();
    resolve(service);
    await Promise.resolve();
    expect(document.querySelector('.custom-dress-section')).toBeNull();
  });
});
