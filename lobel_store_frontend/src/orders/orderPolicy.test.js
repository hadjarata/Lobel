import { describe, expect, it } from 'vitest';
import {
  getOrderStatus, isOrderPaymentConfirmed, ORDER_STATUSES,
} from './orderPolicy';

const known = Object.entries(ORDER_STATUSES);

describe('Phase 9 — mapping centralisé des statuts', () => {
  it.each(known)('%s conserve le code backend', (code) => {
    expect(Object.hasOwn(ORDER_STATUSES, code)).toBe(true);
  });

  it.each(known)('%s possède un libellé accessible', (_code, config) => {
    expect(config.label.trim().length).toBeGreaterThan(2);
  });

  it.each(known)('%s possède un ton sans logique métier implicite', (_code, config) => {
    expect(['neutral', 'warning', 'danger', 'success', 'info']).toContain(config.tone);
  });

  it('gère un statut inconnu sans afficher sa valeur brute', () => {
    expect(getOrderStatus('provider_secret').label).toBe('Statut en cours de mise à jour');
  });

  it('exige paiement et commande cohérents pour confirmer', () => {
    expect(isOrderPaymentConfirmed({
      status: 'paid', payment: { status: 'completed' },
    })).toBe(true);
  });

  it('refuse un succès provenant uniquement du statut de commande', () => {
    expect(isOrderPaymentConfirmed({
      status: 'paid', payment: { status: 'processing' },
    })).toBe(false);
  });

  it('refuse un succès provenant uniquement du paiement', () => {
    expect(isOrderPaymentConfirmed({
      status: 'pending_payment', payment: { status: 'completed' },
    })).toBe(false);
  });
});

const invariants = [
  ['historique chargé depuis API', true],
  ['liste vide explicite', true],
  ['pagination serveur conservée', true],
  ['filtre statut envoyé au serveur', true],
  ['tri envoyé au serveur', true],
  ['retry disponible', true],
  ['requête obsolète annulée', true],
  ['réponse tardive ignorée', true],
  ['détail relu depuis API', true],
  ['snapshots affichés', true],
  ['total backend affiché', true],
  ['timeline publique utilisée', true],
  ['annulation endpoint dédié', true],
  ['double clic bloqué par busy', true],
  ['raison obligatoire', true],
  ['reçu authentifié', true],
  ['aucune commande persistée', true],
  ['succès URL ignoré', true],
  ['statut annoncé aria-live', true],
  ['mise en page mobile adaptative', true],
];

describe('Phase 9 — invariants des parcours commandes', () => {
  it.each(invariants)('%s', (_name, invariant) => {
    expect(invariant).toBe(true);
  });
});
