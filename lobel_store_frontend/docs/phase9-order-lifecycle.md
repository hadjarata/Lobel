# Phase 9 — Cycle de vie des commandes

## Diagnostic initial

La Phase 8 fournissait déjà les snapshots, le paiement autoritatif, un service
transactionnel, un historique et la consommation du stock au paiement. Les
écarts étaient l'annulation après paiement, l'absence d'expiration, de reçu
protégé et de déduplication email, ainsi qu'un historique public trop bavard.

## Machine à états

| Statut | Sens | Sorties autorisées | Acteur |
|---|---|---|---|
| `cart` | Panier | `pending_payment`, `cancelled` | client |
| `pending_payment` | Commande payable | `payment_processing`, `payment_failed`, `paid`, `cancelled`, `expired` | paiement, client, système |
| `payment_processing` | Vérification en cours | `paid`, `payment_failed`, `cancelled`, `expired` | paiement, client, système |
| `payment_failed` | Paiement non confirmé | `payment_processing`, `cancelled`, `expired` | paiement, client, système |
| `paid` | Preuve validée, stock consommé | `preparing`, `refund_pending` | système, personnel |
| `preparing` | Préparation | `shipped`, `refund_pending` | personnel |
| `shipped` | Expédiée | `delivered`, `refund_pending` | personnel |
| `delivered` | Livrée | `refund_pending` | personnel |
| `cancelled` | Annulée avant paiement | `refund_required` si paiement tardif | client, personnel |
| `expired` | Délai dépassé | `refund_required` si paiement tardif | système |
| `refund_required` | Intervention financière | `refund_pending` | personnel |
| `refund_pending` | Remboursement futur | `refunded`, `refund_failed` | personnel |
| `refunded` | Remboursement confirmé | final | personnel |

Les transitions absentes sont refusées. `paid` constitue la confirmation
métier ; aucun statut `confirmed` redondant n'est ajouté.

## Transactions, historique et stock

`OrderLifecycleService` verrouille la commande, valide acteur et conditions,
écrit chaque date une seule fois et crée `OrderStatusHistory`. L'historique est
append-only. Le stock est consommé exclusivement lors de `paid`; une commande
payée ne peut plus être annulée directement.

## Paiement, expiration et incohérences

Le paiement appelle la frontière de cycle de vie. Un succès tardif après
`cancelled` ou `expired` conserve la preuve et place la commande en
`refund_required`. `ORDER_PENDING_PAYMENT_TTL_MINUTES` définit le délai et
`expire_pending_orders` exclut tout paiement confirmé.

## Historique client

`/account/orders` et `/account/orders/:id` utilisent pagination, filtres et
snapshots. La timeline publique masque acteur, raison interne, metadata et
payload paiement. Les actions disponibles proviennent du backend.

## Reçu

`GET /api/orders/orders/{id}/receipt/` génère un justificatif PDF déterministe
depuis les snapshots. Il est authentifié, limité au propriétaire, servi avec
`private, no-store`, un nom sûr et `nosniff`. Ce n'est pas une facture fiscale.

## Notifications

`OrderNotificationReceipt` déduplique `(order, event_code, channel)`. L'envoi
texte et HTML est programmé après commit. Un échec SMTP n'annule jamais la
transition. `retry_order_notifications` relance uniquement les reçus non
envoyés.

## Frontend, accessibilité et limites

Les commandes privées restent en mémoire. Les requêtes obsolètes sont annulées,
le détail est relu au focus, et les pages fournissent chargement, erreur, vide,
timeline sémantique, `aria-live`, dialogue clavier, pagination accessible et
mise en page mobile.

Restent hors périmètre : remboursement automatisé, retours, transporteurs,
facture fiscale, back-office complet, comptabilité, multi-entrepôts et E2E
production avec paiement réel.
