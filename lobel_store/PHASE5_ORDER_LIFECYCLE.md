# Phase 5 — cycle de vie des commandes

## États et transitions

```text
CART
  ├──> PENDING_PAYMENT ──> PAID ──> PREPARING ──> SHIPPED ──> DELIVERED
  │          └──> CANCELLED   ├──> CANCELLED
  └──> CANCELLED             └──> REFUND_PENDING ──> REFUND_FAILED
                                      └──> REFUNDED (confirmation technique future)
```

Pour la compatibilité de données anciennes uniquement, une preuve de paiement
vérifiée peut convertir directement un ancien `CART` en `PAID`.

| État | Sens | Terminal | Stock consommé possible |
|---|---|---:|---:|
| `CART` | panier modifiable | non | non |
| `PENDING_PAYMENT` | snapshots figés, paiement attendu | non | non |
| `PAID` | paiement vérifié | non | oui |
| `PREPARING` | préparation logistique | non | oui |
| `SHIPPED` | remis au transport | non | oui |
| `DELIVERED` | livré | oui | oui |
| `CANCELLED` | annulé selon les règles | oui | non ou restauré |
| `REFUND_PENDING` | demande financière enregistrée | non | oui |
| `REFUND_FAILED` | tentative future échouée | non | oui |
| `REFUNDED` | remboursement techniquement confirmé | oui | oui |

## Frontière métier et historique

`OrderLifecycleService.transition_order()` verrouille la commande avec
`select_for_update()`, valide la matrice, les permissions et les préconditions,
applique les effets de stock, écrit les dates serveur et ajoute un
`OrderStatusHistory` dans la même transaction.

L’historique conserve l’ancien et le nouvel état, l’acteur, son rôle au moment
de l’action, le motif stable, une note et des métadonnées. Il est en lecture
seule dans l’API et dans l’administration, où le statut est également non
modifiable.

## Permissions

- Le propriétaire peut annuler `CART` ou `PENDING_PAYMENT`.
- Le personnel peut annuler `PAID` ou `PREPARING`, puis préparer, expédier et
  livrer via les endpoints métier.
- Le propriétaire ou le personnel peut demander un remboursement admissible.
- `REFUNDED` exige une confirmation technique explicite et n’est exposé par
  aucun endpoint client.

Les endpoints sont `cancel`, `prepare`, `ship`, `deliver` et `request-refund`.
Une commande appartenant à un autre client reste invisible (`404`).

## Stock, annulation et remboursement

`stock_consumed_at` prouve le décrément et `stock_released_at` prouve la
restauration. Une annulation avant paiement ne touche pas au stock. Une
annulation autorisée après paiement verrouille les variantes exactes et restaure
une seule fois les quantités. Un second appel identique est idempotent.

Un remboursement financier n’implique jamais automatiquement un retour
physique. Cette phase enregistre seulement la demande et ses transitions; aucun
appel fournisseur et aucune réception de retour ne sont simulés.

## Migration

La migration convertit explicitement :

- `pending` vers `CART` sans snapshot, sinon `PENDING_PAYMENT`;
- `paid` vers `PAID`;
- `cancelled` vers `CANCELLED`;
- `refunded` vers `REFUNDED`;
- l’ancien `failed` ambigu vers `CANCELLED`, choix prudent sans réalité
  logistique inventée.

Une seule entrée `legacy_backfill` est créée par commande. Aucune chronologie
fictive ni suppression historique n’est produite.

## Limites

Le remboursement fournisseur, les retours physiques, le transporteur,
l’expiration automatique des paiements, les notifications et l’audit
administratif avancé restent hors périmètre.
