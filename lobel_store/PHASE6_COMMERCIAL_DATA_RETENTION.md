# Phase 6 — conservation des données commerciales

## Politique

Les commandes, lignes, paiements, événements financiers, historiques de statut
et snapshots sont conservés sans suppression automatique dans l’application
ordinaire. Les produits, variantes, catégories, collections et comptes clients
sont retirés de l’usage par désactivation ou archivage.

Les sessions, caches, paniers vides anciens, données de test et journaux sans
valeur commerciale pourront relever d’une future purge technique séparée. Aucun
service de purge commerciale n’est exposé par l’API ou l’administration.

La durée légale ou contractuelle définitive devra être validée selon le pays
d’exploitation et les obligations comptables applicables. Aucune durée ni
suppression automatique n’est configurée avant cette validation.

## Niveaux de protection

- Les ViewSets de commandes et paiements sont en lecture seule : `DELETE`
  retourne `405`.
- `Order`, `Payment`, `PaymentWebhookEvent` et `OrderStatusHistory` refusent
  `delete()` et `QuerySet.delete()`.
- Les clés étrangères commerciales utilisent `PROTECT`.
- L’administration masque les suppressions, y compris pour les superusers.
- Une suppression de client détache la commande avec `SET_NULL`; les snapshots,
  lignes et paiements restent présents.

## Matrice `on_delete`

| Relation | Avant | Après | Justification |
|---|---|---|---|
| `OrderItem.order → Order` | `CASCADE` | `PROTECT` | Préserver chaque ligne |
| `Payment.order → Order` | `CASCADE` | `PROTECT` | Préserver la preuve financière |
| `OrderStatusHistory.order → Order` | `PROTECT` | `PROTECT` | Préserver la traçabilité |
| `Order.customer → Customer` | `SET_NULL` | `SET_NULL` | Vente autonome du compte |
| `OrderItem.product → Product` | `SET_NULL` | `SET_NULL` | Snapshots autonomes |
| `OrderItem.variant → ProductVariant` | `SET_NULL` | `SET_NULL` | Snapshots autonomes |
| `PaymentWebhookEvent.payment → Payment` | `SET_NULL` | `SET_NULL` | Événement autonome |
| `Product.category → Category` | `CASCADE` | `PROTECT` | Empêcher la perte des produits |
| `ProductVariant.product → Product` | `CASCADE` | `CASCADE` contrôlé | Dépendance catalogue; suppression produit absente de l’API/admin |
| `ProductMedia.product → Product` | `CASCADE` | `CASCADE` contrôlé | Média sans valeur commerciale autonome |
| `Customer.user → User` | `CASCADE` | `CASCADE` | Profil d’authentification; commandes détachées avant cascade |

Les cascades catalogue restantes ne peuvent pas effacer une commande, une ligne
ou une preuve financière. Elles ne sont accessibles que lors d’une intervention
technique physique hors fonctionnement ordinaire.

## Archivage du catalogue

Une catégorie inactive est masquée publiquement sans modifier ses produits.
Un produit archivé devient inactif et désactive ses variantes dans une
transaction. Une variante inactive ne peut plus être ajoutée au panier.

Les endpoints `archive` et `reactivate` et les actions d’administration
remplacent la suppression. La réactivation d’un produit exige une catégorie
active. Les anciennes commandes continuent d’utiliser leurs snapshots.

## Maintenance exceptionnelle

Une éventuelle purge future devra porter un nom explicite, vérifier l’absence de
toute référence commerciale, être indisponible en production ordinaire et
produire un journal d’audit. Cette phase ne crée volontairement aucun tel
mécanisme.
