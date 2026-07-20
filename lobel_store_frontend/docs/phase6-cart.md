# Phase 6 — Variantes et panier

## 1. Diagnostic initial

Le frontend utilisait deux architectures concurrentes : appels directs dans la
page panier et stockage `lobel_guest_cart`. Il persistait des snapshots produit,
un compteur séparé et un total invité recalculé. La fusion exécutait une boucle
de `POST`/`PUT`, sans transaction ni idempotence. La fiche sélectionnait la
première variante disponible même lorsque plusieurs choix existaient.

## 2. Contrat backend panier

| Fonction | Méthode | Endpoint | Corps | Réponse | Erreurs | Auth |
|---|---|---|---|---|---|---|
| Lire le panier | GET | `/api/orders/orders/cart/` | — | panier complet ou vide | 401 | oui |
| Ajouter | POST | `/api/orders/order-items/` | `variant_id`, `quantity` | ligne serveur | quantité, produit, variante, stock | oui |
| Modifier | PATCH | `/api/orders/order-items/{id}/` | `quantity` | ligne serveur | 400, 404, stock | oui |
| Supprimer | DELETE | `/api/orders/order-items/{id}/` | — | 204 | 404, panier figé | oui |
| Vider | DELETE | `/api/orders/orders/cart/clear/` | — | panier vide | panier figé | oui |
| Fusionner | POST | `/api/orders/orders/cart/merge/` | `items[]` | panier + rapport | 400, 409 | oui |
| Résoudre variantes | POST | `/api/products/products/resolve-variants/` | `variant_ids[]` | variantes + absentes | 400 | non |

`CartService` applique les transactions, verrouille client, panier, lignes et
variantes, déduit le prix de `effective_price` et ne consomme aucun montant
client. Les contraintes garantissent un panier actif par client et une ligne
par variante.

## 3. Architecture frontend retenue

`CartProvider` encapsule API et stockage. Il expose état, panier, lignes,
compteur d'unités, mutations, vidage, rechargement et fusion. Les composants ne
connaissent ni Axios ni `localStorage`. Une génération de session et des verrous
par ligne empêchent réponses tardives et doubles soumissions.

## 4. Modèle des variantes

Le modèle normalisé contient `id`, `product_id`, `product_name`, `sku`, `color`,
`size`, `attributes`, `price`, `stock`, `is_available` et `image`. Le prix reste
une chaîne décimale et un stock absent invalide le contrat. Une sélection
automatique n'a lieu que lorsqu'une seule variante est disponible. Les valeurs
compatibles proviennent toujours de variantes réelles.

## 5. Panier invité

La clé unique est `lobelstore.guest-cart.v1`. Chaque ligne ne conserve que
`variant_id`, `quantity` et `added_at`; le conteneur ajoute identifiant,
révision et clé de fusion temporaire. Aucun token, total, prix, stock ou donnée
personnelle n'est persisté. Lecture, corruption, déduplication, 50 lignes et
quantité maximale 99 sont validées.

Les variantes sont rafraîchies en une requête groupée. Une variante absente ou
un conflit de stock reste visible comme erreur : rien n'est supprimé
silencieusement.

## 6. Panier connecté

Le panier connecté vient uniquement de Django. Après chaque mutation confirmée,
le contexte recharge le panier complet. Les montants restent ceux des
serializers. Au logout ou changement d'utilisateur, la génération courante est
invalidée et aucun panier serveur n'est copié vers le stockage invité.

## 7. Fusion

La fusion démarre après restauration du profil authentifié. Le client conserve
une clé stable tant que le contenu ne change pas. Le backend verrouille le
client, déduplique par `variant_id`, fusionne dans une transaction et mémorise
le rapport dans `CartMergeReceipt`.

La politique est partielle : lignes valides fusionnées, quantités plafonnées au
stock avec rapport, lignes absentes/inactives rejetées. Le frontend retire du
stockage uniquement les quantités confirmées et conserve les restes/rejets.
Une panne réseau conserve intégralement le panier et la clé pour réessai.

## 8. Montants et stock

Le frontend n'envoie que `variant_id` et `quantity`. Le panier invité affiche
le prix unitaire rafraîchi mais aucun total de ligne ou de panier calculé. Le
panier connecté affiche `unit_price`, `line_total`, `cart_total` et `currency`
du backend. Le stock affiché est informatif et chaque mutation est revalidée.

## 9. Modifications par fichier

Frontend :

- `src/cart/*` : contexte, stockage, erreurs, constantes et modèle variante.
- `src/api/cart.js` et `endpoints.js` : API serveur centralisée.
- `src/pages/Product/Product.jsx` : sélection non ambiguë et ajout centralisé.
- `src/pages/Cart/Cart.jsx` : états, lignes invalides et montants autoritatifs.
- `src/components/layout/Navbar.jsx` : compteur global d'unités.
- `src/main.jsx` : installation du provider.
- `package.json` et CI : commande `test:cart`.

Backend :

- `orders/models.py` et migration 0009 : reçus d'idempotence.
- `orders/services/cart_service.py` : fusion, erreurs structurées et vidage.
- `orders/views.py`/`serializers.py` : endpoints et validation.
- `products/views.py` : résolution groupée publique.
- tests `tests_cart_merge.py` et `tests_variant_resolver.py`.

## 10. Accessibilité et responsive

Les groupes de variantes utilisent `fieldset`/`legend`, `aria-pressed` et des
états `disabled`. Le panier annonce mutations et suppressions, nomme les
boutons quantité, associe les erreurs aux lignes et désactive la poursuite si
une ligne est invalide. La mise en page existante reste en cartes responsives.

## 11. Tests

Vitest exécute 86 tests panier dédiés et 262 tests frontend au total :
stockage, corruption, limites, variante, compatibilité, erreurs, restauration,
mutations invitées/connectées, fusion, conservation après panne et double ajout.
Django exécute 182 tests, dont 16 nouveaux sur fusion/résolution.

Playwright n'est pas installé : aucun test E2E navigateur n'a été ajouté.

## 12. CI

Le workflow exécute désormais `test:cart` après environnement, authentification,
contrats et catalogue, avant la suite complète, le build et `npm audit`.

## 13. Résultats des commandes

- Node/npm, `npm ci`, lint et toutes les suites spécialisées : réussis.
- `npm test` : 262/262.
- build production : réussi.
- `npm audit` : aucune vulnérabilité connue.
- Django check et migrations sèches : réussis.
- Django : 182/182.
- OpenAPI régénéré ; seuls les deux avertissements historiques d'operationId
  dupliqués pour les alias JWT subsistent.

## 14. Validation manuelle

Les parcours ont été validés par tests DOM et API isolés : variante unique,
variantes multiples, combinaison impossible, persistance, ajout répété,
quantité, suppression, vide, fusion complète/partielle, panne et changement de
session. L'absence de navigateur pilotable empêche une validation visuelle
réelle aux largeurs 320–1366 px et un parcours clavier complet.

## 15. Problèmes non corrigés

Création définitive de commande, adresses, livraison, promotions, taxes,
checkout complet, LigdiCash, retour paiement, remboursements, favoris,
optimisation générale du bundle/médias et back-office restent hors périmètre.

## 16. Vérification du périmètre

Aucun paiement ou commande définitive n'est créé. Aucun total autoritatif n'est
calculé ou transmis. Tout ajout utilise `variant_id`. Les permissions, JWT,
configuration de production, catalogue et contrats antérieurs sont préservés.

## 17. Verdict

Les variantes, le panier invité, le panier connecté et la fusion disposent
désormais d'une source de vérité, d'une idempotence durable et de protections
de concurrence suffisantes pour commencer la Phase 7. La future phase devra
consommer le panier serveur final sans réintroduire de calcul client.

