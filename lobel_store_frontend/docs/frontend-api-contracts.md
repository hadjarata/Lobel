# Contrats API frontend LobelStore

Ce document décrit les contrats consommés par le frontend après la Phase 4.
Le backend Django/DRF, ses serializers et ses tests restent la source de
vérité. L’URL de base provient exclusivement de `VITE_API_BASE_URL`.

## Conventions communes

- Authentification privée : `Authorization: Bearer <access>`.
- Pagination DRF : `{ count, next, previous, results }`.
- Paramètres de pagination : `page` et `page_size` (maximum serveur : 100).
- Noms de champs : le frontend conserve le `snake_case` du backend.
- Dates : chaînes ISO 8601 UTC, affichées dans le fuseau local du navigateur.
- Montants : chaînes décimales, jamais recalculées comme source autoritative.
- Devise commerciale actuelle : `XOF`.
- Médias : `url` pour `PublicMediaSerializer`; URL absolue conservée, URL
  relative résolue avec la configuration API.
- Erreurs : `detail`, erreurs par champ, `non_field_errors`, `code` et
  `Retry-After` sont normalisés par `normalizeApiError`.

## Matrice frontend/backend

| Domaine | Service frontend | Méthode et endpoint backend | Sortie | Statut |
|---|---|---|---|---|
| Auth | `login` | `POST /api/auth/login/` | JWT access/refresh | Conforme |
| Auth | `refreshSession` | `POST /api/auth/refresh/` | JWT tournés | Conforme |
| Auth | `logout` | `POST /api/auth/logout/` | 204 | Conforme |
| Client | `getCurrentUser` | `GET /api/users/customers/me/` | détail client | Conforme |
| Client | `updateCustomerProfile` | `PATCH /api/users/customers/{id}/` | détail client | Conforme |
| Produit | `getProducts` | `GET /api/products/products/` | page de résumés | Conforme |
| Produit | `getProductById` | `GET /api/products/products/{id}/` | détail | Conforme |
| Produit | `getNewProducts` | `GET /api/products/products/new/` | page de résumés | Conforme |
| Produit | `getBestSellers` | `GET /api/products/products/bestsellers/` | page de résumés | Conforme |
| Produit | `searchProducts` | `GET /api/products/products/?search=` | page de résumés | Conforme |
| Catégorie | `getCategories` | `GET /api/products/categories/` | page | Conforme |
| Catégorie | `getProductsByCategory` | `GET /api/products/products/?category=` | page | Corrigé |
| Collection | `getCollections` | `GET /api/products/collections/` | page | Conforme |
| Collection | `getProductsByCollection` | `GET /api/products/products/?collection=` | page | Corrigé |
| Panier | `fetchCart` | `GET /api/orders/orders/cart/` | détail commande ou panier vide | Conforme |
| Ligne panier | `addToCart` | `POST /api/orders/order-items/` | ligne; entrée `variant_id`, `quantity` | Corrigé |
| Ligne panier | `updateCartItemQuantity` | `PUT /api/orders/order-items/{id}/` | ligne | Conforme |
| Ligne panier | `removeCartItem` | `DELETE /api/orders/order-items/{id}/` | 204 | Conforme |
| Commande | `getOrders` | `GET /api/orders/orders/` | page de résumés sans lignes | Conforme |
| Commande | `getOrderById` | `GET /api/orders/orders/{id}/` | détail avec lignes | Conforme |
| Paiement | `getPayments` | `GET /api/payments/payments/` | page de résumés | Conforme |
| Paiement | `getPaymentById` | `GET /api/payments/payments/{id}/` | détail | Conforme |
| Checkout | `initiateCheckout` | `POST /api/payments/checkout/` | session de redirection | Conforme |
| Mock paiement | `confirmMockPayment` | `POST /api/payments/mock/confirm/` | confirmation | Dev/test uniquement |

Les anciens `POST /api/payments/payments/`, `PUT /api/payments/payments/{id}/`,
`DELETE /api/orders/order-items/` et endpoint catégorie dédié aux produits ont
été retirés : ils n’existent pas dans les viewsets actuels.

## Produits, variantes et médias

La liste utilise `ProductListSerializer` et ne contient ni description ni
liste complète des médias. Le détail utilise `ProductDetailSerializer`.

Une variante est identifiée par `id`; elle expose `color`, `size`, `stock`,
`is_active`, `sku` et un éventuel `price`. L’ajout serveur attend
obligatoirement `variant_id`, jamais `product_id`.

`media_files` contient `{id, media_type, url, order, width, height,
duration_seconds}`. Les anciens champs `file` et `file_url` ne sont utilisés
qu’en tolérance dans l’utilitaire média, pas comme contrat principal.

Filtres produits autorisés : `search`, `category`, `collection`, `available`,
`min_price`, `max_price`, `color`, `size` et `ordering`. Les champs de tri sont
`name`, `price`, `date_created` et `sales_count`.

## Profil

Le profil contient `id`, `user`, `country`, `phone_number`, `address` et
`date_created`. `user` contient `id`, `username`, `first_name`, `last_name`,
`email` et `is_active`.

La mise à jour accepte uniquement `first_name`, `last_name`, `country`,
`phone_number` et `address`. Les autres champs sont en lecture seule.

## Commandes et panier

`OrderListSerializer` ne contient pas `items`. Le clic sur une commande charge
donc explicitement son détail.

Une ligne expose les snapshots `product_name`, `variant_name`, `color`, `size`,
`sku`, `unit_price`, `line_total`, `subtotal`, `currency` et les références.
Les écrans utilisent ces montants serveur et ne recalculent plus le total de
ligne.

Le panier vide est explicitement `{id:null, items:[], cart_total:0,
cart_items:0, complete:false, status:"pending"}`. Un panier existant suit le
serializer de détail de commande.

## Paiements

Le viewset paiement est en lecture seule. La liste contient un résumé de
commande; le détail contient la commande complète. Les statuts actuels sont
`pending`, `completed` et `failed`; les providers sont `manual`, `mock` et
`ligdicash`.

Le checkout accepte `frontend_url` et renvoie `payment_url`, `sessionToken`,
`paymentId` et `orderId`. L’URL de paiement doit être HTTP(S). Le frontend ne
considère pas les paramètres de retour comme preuve de paiement.

## Limites reportées

La Phase 5 doit encore traiter la pagination et les filtres dans l’interface
catalogue. Les phases panier et checkout devront terminer la fusion invitée,
les conflits de stock, l’idempotence et le retour LigdiCash. Les mocks produit
historiques encore présents dans le composant de détail sont inaccessibles
après validation stricte du contrat, mais leur suppression complète reste à
faire avec la refonte catalogue.

## Contrat paiement Phase 8

`POST /api/payments/checkout/` reçoit uniquement `order_id` et l'en-tête
`Idempotency-Key`. Le montant, la devise et la référence sont dérivés de la
commande verrouillée côté backend. La réponse publique n'expose ni jeton
fournisseur, ni secret, ni payload brut.

`POST /api/payments/payments/{id}/refresh-status/` confirme l'état directement
auprès du fournisseur. `POST /api/payments/payments/{id}/redirected/` enregistre
la redirection sans modifier l'état financier.

Le retour navigateur est non autoritatif : ses paramètres sont ignorés et
supprimés. Le frontend reprend uniquement l'identifiant interne sauvegardé et
n'affiche le succès qu'après confirmation backend `completed` et commande
`paid`. Les mutations de paiement ne sont jamais rejouées automatiquement
après un rafraîchissement JWT.

## Contrat commandes Phase 9

La liste paginée expose `item_count`, `payment_status`, `can_pay` et
`can_cancel`. Le détail expose les snapshots, une timeline publique filtrée,
le paiement public et `available_actions`.

- `POST /api/orders/orders/{id}/cancel/` accepte une raison et revérifie
  propriétaire, statut et paiement.
- `GET /api/orders/orders/{id}/receipt/` télécharge un justificatif HTML
  authentifié depuis les snapshots.

Le client ne reçoit ni acteur d'audit, ni raison interne, ni metadata, ni
payload fournisseur. Il n'envoie jamais de statut de commande.
