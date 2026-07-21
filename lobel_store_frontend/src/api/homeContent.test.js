import { describe, expect, it } from 'vitest';
import { adaptHomeHero } from './homeContent';

describe('adaptHomeHero', () => {
  it('adapte le contrat minimal image', () => {
    expect(adaptHomeHero({
      title: ' Bienvenue ',
      description: ' Découvrez LobelStore. ',
      media_type: 'IMAGE',
      media_url: 'https://cdn.example.com/hero.webp',
    })).toEqual({
      title: 'Bienvenue',
      description: 'Découvrez LobelStore.',
      mediaType: 'IMAGE',
      mediaUrl: 'https://cdn.example.com/hero.webp',
    });
  });

  it('adapte le contrat minimal vidéo', () => {
    expect(adaptHomeHero({
      title: 'Bienvenue',
      description: 'Découvrez LobelStore.',
      media_type: 'VIDEO',
      media_url: 'https://cdn.example.com/hero.mp4',
    })).toMatchObject({
      mediaType: 'VIDEO',
      mediaUrl: 'https://cdn.example.com/hero.mp4',
    });
  });

  it.each([
    null,
    {},
    { title: '', description: 'Texte', media_type: 'IMAGE', media_url: '/x.jpg' },
    { title: 'Titre', description: '', media_type: 'IMAGE', media_url: '/x.jpg' },
    { title: 'Titre', description: 'Texte', media_type: 'AUDIO', media_url: '/x' },
    { title: 'Titre', description: 'Texte', media_type: 'IMAGE', media_url: null },
  ])('rejette une configuration invalide %#', (value) => {
    expect(adaptHomeHero(value)).toBeNull();
  });

  it('ignore complètement les anciens champs éditoriaux', () => {
    const adapted = adaptHomeHero({
      title: 'Titre',
      description: 'Description',
      media_type: 'IMAGE',
      media_url: '/hero.jpg',
      eyebrow: 'Ancien surtitre',
      primary_button: { label: 'Danger', url: '/danger' },
      secondary_button: { label: 'Secondaire', url: '/secondaire' },
      desktop_image_url: '/old.jpg',
      mobile_image_url: '/mobile.jpg',
      video_poster_url: '/poster.jpg',
    });

    expect(adapted).toEqual({
      title: 'Titre',
      description: 'Description',
      mediaType: 'IMAGE',
      mediaUrl: '/hero.jpg',
    });
  });
});
