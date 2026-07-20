# Phase 5 — Fiabilisation du catalogue

## 1. Résultat

Le catalogue est désormais piloté par le serveur et partageable par URL. Les
produits ne sont plus filtrés à partir d'une première page locale.

## 2. Audit initial

L'ancienne boutique chargeait une page puis filtrait en mémoire. Le nombre de
pages était fixé à `1`, les facettes provenaient de cette page, recherche et
tri n'étaient pas connectés à l'API et la fiche conservait des produits simulés.

## 3. Contrat serveur

- Liste : `GET /api/products/products/`
- Facettes : `GET /api/products/products/filter-options/`
- Détail : `GET /api/products/products/{id}/`
- Nouveautés : `GET /api/products/products/new/`
- Meilleures ventes : `GET /api/products/products/bestsellers/`

La page boutique contient 24 produits. Les tris visibles sont traduits vers la
liste blanche backend (`date_created`, `price`, `name`, `sales_count`).

## 4. URL canonique

Paramètres : `page`, `q`, `sort`, `category`, `collection`, `min_price`,
`max_price`, `color`, `size`, `available`. Les défauts sont omis et les valeurs
invalides sont nettoyées. Un changement de critère remet la page à 1.

## 5. Recherche et concurrence

La saisie est temporisée à 350 ms et la validation du formulaire est immédiate.
Une navigation annule la requête précédente via `AbortController`; un numéro
de séquence empêche aussi une réponse tardive de remplacer la réponse courante.

## 6. Facettes

L'endpoint est indépendant de la pagination. Il renvoie les catégories et
produits publics, collections actives dans leur période, couleurs/tailles
portées par une variante active en stock, ainsi que la plage de prix.

## 7. États d'interface

Chargement, erreur récupérable, résultat vide et succès sont distincts. Le
compteur vient de `count`. Une page hors limites est corrigée vers la dernière.

## 8. Accessibilité

La recherche est libellée, les sections sont des boutons avec `aria-expanded`,
la feuille mobile est un dialogue fermé par Échap, les résultats ont une zone
`aria-live` et la pagination conserve `aria-current`.

## 9. Responsive

Le panneau latéral devient une feuille sous 768 px. La barre de résultats passe
en colonne et la grille conserve ses règles responsive.

## 10. Cartes produit

Une carte ne choisit jamais une variante implicitement : son action ouvre la
fiche. Les vidéos éventuelles ne démarrent plus automatiquement.

## 11. Fiche produit

Les données simulées et compatibilités avec l'ancien format ont été retirées.
Détail, médias et variantes viennent du contrat strict. Les suggestions sont
une requête serveur limitée à la catégorie courante.

## 12. Accueil

Nouveautés et meilleures ventes utilisent leurs endpoints dédiés et paginés.
Les collections restent une sélection visuelle limitée.

## 13. Tests frontend

`npm run test:catalog` exécute 70 cas : URL, invalides, paramètres API, pages,
prix, concurrence, annulation et accessibilité de la pagination.

## 14. Tests backend

Deux cas couvrent les facettes complètes et l'exclusion des variantes hors
stock. La suite backend compte 166 tests.

## 15. CI

Le job frontend exécute explicitement `npm run test:catalog` avant la suite
complète et le build production.

## 16. Validation

- `npm run test:catalog` : 70/70
- `npm test` : 176/176
- `npm run lint` : réussi
- `npm run build:production` : réussi
- `python manage.py test --keepdb` : 166/166

Le build conserve un avertissement non bloquant sur le bundle principal.

## 17. Limites assumées

Les facettes sont globales, sans compteurs dynamiques par combinaison. La
sélection multiple couleur/taille n'est pas exposée car le backend accepte une
valeur scalaire. Aucun moteur externe, cache de recherche ou tri client n'a été
introduit.
