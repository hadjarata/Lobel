# Runbook Phase 9 — Commandes

## Commande payée mais non confirmée

Inspecter paiement, audit et historique, puis lancer `reconcile_payments` en
dry-run. Ne jamais modifier le statut directement ni demander un second
paiement.

## Paiement après expiration ou annulation

L'état attendu est `refund_required`. Conserver la preuve et ouvrir une
procédure contrôlée. Aucun remboursement n'est automatique.

## Email non envoyé

```bash
python manage.py retry_order_notifications --dry-run --failed-only
python manage.py retry_order_notifications --failed-only
```

Un reçu `sent` ne doit jamais être réinitialisé pour forcer un doublon.

## Commande bloquée

Comparer statut, dernier paiement et historiques. Utiliser les services et
commandes de réconciliation, jamais une modification directe de base.

## Double notification

Vérifier la contrainte unique par commande, événement et canal, puis corriger
le déclencheur sans supprimer l'audit.

## Reçu incorrect

Comparer uniquement les snapshots. Une modification du catalogue ne justifie
jamais le recalcul d'un ancien reçu.
