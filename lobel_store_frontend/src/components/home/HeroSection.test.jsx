import {
  cleanup, fireEvent, render, screen, waitFor,
} from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import {
  afterEach, beforeEach, describe, expect, it, vi,
} from 'vitest';
import HeroSection from './HeroSection';
import { getHomeHero } from '../../api/homeContent';

vi.mock('../../api/homeContent', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, getHomeHero: vi.fn() };
});

const imageHero = {
  title: 'Titre administré',
  description: 'Description administrée',
  mediaType: 'IMAGE',
  mediaUrl: 'https://cdn.example.com/hero.webp',
};
const videoHero = {
  ...imageHero,
  mediaType: 'VIDEO',
  mediaUrl: 'https://cdn.example.com/hero.mp4',
};

const renderHero = () => render(
  <MemoryRouter><HeroSection /></MemoryRouter>,
);

let reduceMotion = false;
const mediaStates = new WeakMap();

beforeEach(() => {
  reduceMotion = false;
  Object.defineProperty(document, 'hidden', { configurable: true, value: false });
  window.matchMedia = vi.fn().mockImplementation(() => ({
    matches: reduceMotion,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  Object.defineProperty(HTMLMediaElement.prototype, 'paused', {
    configurable: true,
    get() { return mediaStates.get(this) ?? true; },
  });
  HTMLMediaElement.prototype.play = vi.fn(function play() {
    mediaStates.set(this, false);
    this.dispatchEvent(new Event('play'));
    return Promise.resolve();
  });
  HTMLMediaElement.prototype.pause = vi.fn(function pause() {
    mediaStates.set(this, true);
    this.dispatchEvent(new Event('pause'));
  });
});

afterEach(cleanup);

describe('Hero minimal administrable', () => {
  it('affiche immédiatement les textes par défaut pendant le chargement', () => {
    getHomeHero.mockReturnValue(new Promise(() => {}));
    renderHero();
    expect(screen.getByRole('heading', { level: 1 }))
      .toHaveTextContent('Bienvenue sur LobelStore');
    expect(screen.getByText(
      'Découvrez notre sélection de créations et explorez notre boutique.',
    )).toBeInTheDocument();
  });

  it('utilise le titre et la description valides du backend', async () => {
    getHomeHero.mockResolvedValue(imageHero);
    renderHero();
    expect(await screen.findByText(imageHero.title)).toBeInTheDocument();
    expect(screen.getByText(imageHero.description)).toBeInTheDocument();
  });

  it('rend uniquement l’image configurée', async () => {
    getHomeHero.mockResolvedValue(imageHero);
    const { container } = renderHero();
    await screen.findByText(imageHero.title);
    expect(container.querySelector('img')).toHaveAttribute('src', imageHero.mediaUrl);
    expect(container.querySelector('video')).not.toBeInTheDocument();
    expect(container.querySelector('picture')).not.toBeInTheDocument();
  });

  it('rend uniquement la vidéo configurée sans poster', async () => {
    getHomeHero.mockResolvedValue(videoHero);
    const { container } = renderHero();
    await screen.findByText(videoHero.title);
    expect(container.querySelector('video')).toBeInTheDocument();
    expect(container.querySelector('video')).not.toHaveAttribute('poster');
    expect(container.querySelector('img')).not.toBeInTheDocument();
  });

  it('conserve un bouton statique Voir la boutique vers /shop', async () => {
    getHomeHero.mockResolvedValue({
      ...imageHero,
      primaryButton: { label: 'Ancien bouton', url: '/danger' },
    });
    renderHero();
    expect(await screen.findByRole('link', { name: 'Voir la boutique' }))
      .toHaveAttribute('href', '/shop');
    expect(screen.queryByText('Ancien bouton')).not.toBeInTheDocument();
  });

  it('affiche un indicateur de scroll vers les nouveautés', () => {
    getHomeHero.mockReturnValue(new Promise(() => {}));
    renderHero();
    expect(screen.getByRole('link', { name: 'Découvrir les nouveautés' }))
      .toHaveAttribute('href', '#new-products');
  });

  it.each([
    ['une erreur API', () => Promise.reject(new Error('network'))],
    ['une configuration absente', () => Promise.resolve(null)],
  ])('utilise le fallback après %s', async (_name, result) => {
    getHomeHero.mockReturnValue(result());
    renderHero();
    expect(screen.getByText('Bienvenue sur LobelStore')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Voir la boutique' }))
      .toHaveAttribute('href', '/shop');
  });

  it('conserve un fond neutre et le contenu après échec de l’image', async () => {
    getHomeHero.mockResolvedValue(imageHero);
    const { container } = renderHero();
    await screen.findByText(imageHero.title);
    fireEvent.error(container.querySelector('img'));
    expect(container.querySelector('img')).not.toBeInTheDocument();
    expect(screen.getByText(imageHero.title)).toBeInTheDocument();
  });

  it('conserve un fond neutre et le contenu après échec de la vidéo', async () => {
    getHomeHero.mockResolvedValue(videoHero);
    const { container } = renderHero();
    await screen.findByText(videoHero.title);
    fireEvent.error(container.querySelector('video'));
    expect(container.querySelector('video')).not.toBeInTheDocument();
    expect(container.querySelector('img')).not.toBeInTheDocument();
    expect(screen.getByText(videoHero.title)).toBeInTheDocument();
  });

  it('désactive la vidéo et son contrôle avec mouvement réduit', async () => {
    reduceMotion = true;
    getHomeHero.mockResolvedValue(videoHero);
    const { container } = renderHero();
    await screen.findByText(videoHero.title);
    expect(container.querySelector('video')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /vidéo/ })).not.toBeInTheDocument();
  });

  it('conserve le contrôle lecture et pause pour une vidéo', async () => {
    getHomeHero.mockResolvedValue(videoHero);
    renderHero();
    fireEvent.click(await screen.findByRole('button', { name: 'Lire la vidéo' }));
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Mettre la vidéo en pause' }));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
  });

  it('met la vidéo en pause lorsque l’onglet est masqué', async () => {
    getHomeHero.mockResolvedValue(videoHero);
    renderHero();
    fireEvent.click(await screen.findByRole('button', { name: 'Lire la vidéo' }));
    Object.defineProperty(document, 'hidden', { configurable: true, value: true });
    document.dispatchEvent(new Event('visibilitychange'));
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
  });

  it('ignore une réponse reçue après démontage', async () => {
    let resolve;
    getHomeHero.mockReturnValue(new Promise((done) => { resolve = done; }));
    const { unmount } = renderHero();
    unmount();
    resolve(imageHero);
    await waitFor(() => expect(screen.queryByText(imageHero.title))
      .not.toBeInTheDocument());
  });
});
