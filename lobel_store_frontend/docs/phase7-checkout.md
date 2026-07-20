# Phase 7 — Checkout et création fiable de commande

## 1. Diagnostic initial

Le checkout relisait le panier puis appelait directement `/api/payments/checkout/`.
Le service de paiement figeait la commande, créait un `Payment` et ouvrait une
session fournisseur dans la même opération. Il n’existait ni adresse structurée,
ni choix de livraison serveur, ni preview versionnée, ni clé d’idempotence de
commande. Une réponse perdue ou deux onglets pouvaient rendre l’issue ambiguë.

## 2. Contrat backend

| Fonction | Méthode | Endpoint | Entrée | Sortie principale |
|---|---|---|---|---|
| Livraison | POST | `/api/orders/orders/checkout/delivery-options/` | adresse | méthodes, frais, délais |
| Preview | POST | `/api/orders/orders/checkout/preview/` | adresse, livraison | lignes, montants, avertissements, version |
| Création | POST | `/api/orders/orders/checkout/create-order/` | preview + `Idempotency-Key` | commande `pending_payment` |
| Reprise | GET | `/api/orders/orders/checkout/pending/` | — | commande du client ou `null` |

Toutes les routes exigent JWT. Les erreurs stables incluent `empty_cart`,
`invalid_cart`, `invalid_delivery_method`, `stale_checkout`,
`invalid_idempotency_key`, `idempotency_conflict` et
`order_already_created`. La commande et la reprise sont filtrées par
`customer__user`.

## 3. Architecture frontend

`Checkout.jsx` est un tunnel à quatre étapes : adresse, livraison,
récapitulatif serveur et commande prête à payer. `src/api/checkout.js`
centralise le contrat. Les POST sont marqués `skipAuthRefresh` : ils ne sont
jamais rejoués automatiquement après un 401. La clé d’idempotence reste stable
pendant une tentative et est renouvelée après une preview obsolète.

Le composant ne persiste ni adresse ni téléphone. Après rechargement, il demande
au backend la dernière commande `pending_payment`. Une commande peut être
annulée via le cycle de commande existant; aucun bouton de paiement actif n’est
exposé pendant cette phase.

## 4. Adresses

Le choix retenu est une adresse saisie au checkout, sans carnet d’adresses.
Le serializer valide nom, téléphone, pays `ML`, ville, rue, longueurs et adresse
de facturation éventuelle. Django copie les champs structurés et la version
affichable dans le snapshot immuable de la commande. Aucun champ personnel
n’est écrit dans `localStorage` ou `sessionStorage`; le profil n’est pas modifié.

## 5. Livraison

`standard` dessert le Mali pour 3 000 XOF, délai 2–5 jours.
`express_bamako` est limité à la ville de Bamako, coûte 1 500 XOF et annonce
0–1 jour. Disponibilité, frais, devise et délais viennent exclusivement de
`OrderCheckoutService`; une méthode forgée ou hors zone est refusée.

## 6. Prévisualisation

L’entrée contient l’adresse et le code de livraison, jamais de prix ni total.
La réponse contient les lignes recalculées, sous-total, livraison, remise, taxe,
total, devise, méthode, avertissements et `checkout_version`. Cette version
SHA-256 canonique couvre lignes, quantités, variantes, prix courants, stock,
activité, adresse et livraison. Toute modification rend la création obsolète.
Une différence avec le prix mémorisé dans le panier produit `price_changed`.

## 7. Création de commande

La transaction verrouille client, panier, lignes et variantes, recalcule la
preview, compare sa version, copie les snapshots produit/variante/prix/adresse,
puis bascule l’objet panier en commande immuable `pending_payment`. Il n’est
alors plus un panier actif ni une source d’affichage mutable; le frontend lit le
serializer de commande. Aucun stock n’est décrémenté ni réservé avant paiement.
Les montants utilisent `Decimal` et les services financiers Django.

## 8. Idempotence

Le navigateur envoie une clé opaque de 64 caractères maximum.
`CheckoutCreationReceipt` la conserve par client avec l’empreinte canonique de
la requête et la commande. La même clé et le même corps rendent la même commande;
un corps différent retourne `idempotency_conflict`. Les reçus sont conservés
avec les données commerciales protégées; aucune purge automatique n’est activée.
Une panne après validation se résout en répétant exactement la même requête.

## 9. Sécurité et concurrence

L’authentification et l’ownership existants restent obligatoires. La source de
vérité est le panier serveur; un invité est arrêté par `PrivateRoute` et par
Django. Le verrou client sérialise deux onglets, la contrainte d’un panier actif
et le reçu interdisent les doublons. Une seconde clé après conversion obtient
`order_already_created`. Les POST de création ne sont pas rejoués par
l’intercepteur JWT et les données d’un utilisateur ne sont jamais reprises pour
un autre.

## 10. Modifications par fichier

Backend :

- `orders/models.py`, migration `0010` : snapshots d’adresse/livraison/version et reçus.
- `orders/serializers.py` : validation structurée et champs de lecture.
- `orders/services/order_checkout_service.py` : livraison, preview, transaction et reprise.
- `orders/views.py` : quatre endpoints authentifiés et erreurs structurées.
- `orders/tests_checkout.py` : prix, stock, idempotence, permissions et non-paiement.

Frontend :

- `src/api/endpoints.js`, `src/api/checkout.js` : contrat et politique de non-rejeu.
- `src/pages/Checkout/Checkout.jsx`/`.css` : tunnel responsive et reprise.
- `src/api/checkout.test.js`, `package.json` : tests dédiés.
- `docs/openapi.generated.yml` : schéma régénéré.
- workflows frontend/backend : étape checkout et correction YAML de production.

## 11. Accessibilité et responsive

Le tunnel utilise `main`, titres hiérarchiques, formulaire natif, labels,
boutons typés, radios groupés, `aria-current` et alerte `role=alert`.
Les contrôles impossibles sont désactivés. Les étapes passent de quatre à deux
colonnes sous 768 px et le formulaire de deux à une colonne.

## 12. Tests

Django couvre 14 scénarios checkout dédiés : zones, frais, preview, prix,
stock, champs obligatoires, snapshot, zéro paiement, même clé, conflit de corps,
seconde clé, reprise, ownership et authentification. Vitest ajoute 5 scénarios
API concernant endpoints, clé et non-rejeu; la suite frontend complète dépasse
les 66 scénarios exigés. Playwright n’est pas installé, donc aucun E2E navigateur
réel n’est ajouté.

## 13. CI

Le workflow frontend lance `test:checkout` avant la suite complète, le build
production et l’audit. Le workflow backend conserve check, migrations sèches et
suite Django/PostgreSQL; l’indentation des variables HSTS du job production a
été corrigée.

## 14. Résultats des commandes

- `manage.py check` et migrations sèches : réussis.
- Django/PostgreSQL : 196/196 tests.
- ESLint : réussi.
- Vitest checkout : 5/5; suite frontend : 267/267.
- Build Vite production avec mock et debug désactivés : réussi.
- `npm audit` : zéro vulnérabilité connue.
- OpenAPI : régénéré avec les quatre routes checkout.

Vite conserve un avertissement non bloquant connu : le bundle JavaScript
principal dépasse 500 kB après minification.

## 15. Validation manuelle

Les parcours sont validés par tests API/DOM automatisés : adresse Bamako/hors
zone, choix de livraison, changement prix/stock, création, double soumission,
reprise et isolation client. La validation visuelle réelle 320–1366 px et le
parcours clavier intégral restent limités par l’absence de navigateur E2E.

## 16. Problèmes non corrigés

Restent hors Phase 7 : initialisation LigdiCash, redirection, retour fournisseur,
webhook, confirmation de paiement, polling, remboursement, back-office,
promotions complexes, optimisation générale, accessibilité globale et E2E
complet de production.

## 17. Vérification du périmètre

Aucun `Payment` n’est créé, aucun statut `paid` n’est posé et aucun stock n’est
consommé. Le frontend n’envoie aucun montant autoritatif et ne persiste aucune
donnée personnelle. La transaction, la version et l’idempotence empêchent les
commandes dupliquées. Permissions, JWT, panier serveur et configuration de
production sont préservés.

## 18. Verdict

Le checkout possède les garanties nécessaires pour aborder la Phase 8 :
entrée authentifiée, validation serveur, livraison et montants autoritatifs,
snapshot immuable, refus des previews obsolètes, création atomique/idempotente
et reprise sûre. La Phase 8 pourra initialiser le paiement uniquement depuis
une commande `pending_payment` déjà figée.
