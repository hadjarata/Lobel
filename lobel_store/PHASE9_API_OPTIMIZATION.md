# Phase 9 — Optimisation de l’API

## Diagnostic et mesures initiales

Toutes les listes DRF étaient non paginées. La liste produit utilisait le même
serializer que le détail. Pour chaque produit, elle rechargeait notamment les
médias, la première image, la première vidéo et les variantes. Les listes de
commandes chargeaient systématiquement les lignes et tout l’historique ; chaque
paiement imbriquait une commande complète.

Mesures PostgreSQL sur les données locales, avec `CaptureQueriesContext` et le
JSON réellement sérialisé :

| Mesure | Avant | Après |
|---|---:|---:|
| Produit liste, 1 objet | 9 requêtes, 1 034 octets | 4 requêtes, 650 octets |
| Produit liste, 9 objets | 81 requêtes, 10 533 octets | 4 requêtes, 5 799 octets |
| Produit détail | N+1 selon relations | 4 requêtes, 865 octets sur l’objet mesuré |
| Commandes liste, 3 objets | 11 requêtes, 6 806 octets | 2 requêtes, 500 octets |

Ces mesures locales caractérisent la requête et le payload ; elles ne sont pas
un benchmark de latence de production.

## Pagination

Toutes les listes potentiellement volumineuses utilisent désormais :

```json
{
  "count": 120,
  "next": "...",
  "previous": null,
  "results": []
}
```

| Endpoint | Défaut | Maximum | Ordre |
|---|---:|---:|---|
| Produits | 20 | 100 | `-date_created, -id` |
| Médias | 20 | 100 | `order, id` |
| Commandes | 20 | 100 | `-date_ordered, -id` |
| Paiements | 20 | 100 | `-date_paid, -id` |
| Collections | 20 | 100 | `-created_at, -id` |
| Catégories | 20 | 100 | `name, id` |

`page_size` doit être positif. Une valeur excessive est plafonnée à 100 ;
zéro, une valeur négative ou non numérique retourne `400`. Une page inexistante
retourne `404`. Le frontend existant savait déjà lire `data.results`, mais ce
format constitue une rupture documentée pour tout autre client qui attendait
un tableau brut.

## Querysets et serializers

La liste produit utilise `ProductListSerializer`. Elle conserve les champs
nécessaires aux cartes et filtres actuels, dont les variantes actives compactes,
mais retire description, galerie, vidéo et métadonnées internes.

Le détail utilise `ProductDetailSerializer` et conserve description, galerie,
vidéos et variantes actives. Les checksums et chemins physiques ne sont pas
exposés publiquement.

`product_queryset()` applique :

- `select_related("category")`;
- un `Exists` pour la disponibilité réelle;
- un prefetch filtré des collections actives;
- un prefetch filtré et ordonné des médias actifs;
- un prefetch des variantes actives avec `color` et `size`;
- `to_attr` afin que les serializers ne relancent aucune requête.

La liste ne précharge que les images, jamais les vidéos. Le détail charge tous
les médias actifs.

Les commandes utilisent un serializer résumé en liste et ne chargent pas
l’historique. Le détail précharge lignes, produit, variante, couleur, taille et
historique. Les paiements utilisent une commande résumée en liste ; le détail
conserve l’ancienne représentation complète.

## Recherche, filtres et tri

| Paramètre | Cible | Validation |
|---|---|---|
| `search` | produit, catégorie, collection, SKU | `icontains`, 100 caractères max |
| `category` | identifiant catégorie | entier |
| `collection` | identifiant ou slug | valeur contrôlée |
| `available` | variante active avec stock | `true/false/1/0` |
| `min_price`, `max_price` | prix produit | décimal positif, intervalle cohérent |
| `color`, `size` | variantes actives | identifiant entier |
| `ordering` | nom, prix, date, ventes | allowlist, préfixe `-` autorisé |

La recherche utilise `distinct()` pour éviter les doublons lorsqu’un produit
correspond via plusieurs variantes. Les produits, catégories, médias et
variantes archivés restent exclus des résultats publics.

## Analyse SQL et index

Le plan PostgreSQL de la liste publique sur le volume actuel utilise des scans
séquentiels et une jointure de hachage. Les coûts estimés restent faibles
(`Sort cost 72.43`, environ 38 lignes estimées). Les clés étrangères, clés
primaires et contraintes uniques fournissent déjà les index relationnels
nécessaires.

| Index envisagé | Décision | Motif |
|---|---|---|
| Produit actif/date | Non ajouté | volume trop faible, scan séquentiel moins coûteux actuellement |
| Variante produit/active/stock | Non ajouté | index FK existant et faible cardinalité |
| Média produit/active/type/ordre | Non ajouté | index FK existant, pages petites |
| Commande client/date | Non ajouté | volume actuel insuffisant pour démontrer le bénéfice |
| Recherche trigramme | Non ajouté | aucune mesure ne justifie `pg_trgm` |

Aucune migration ni aucun coût d’écriture supplémentaire n’a donc été ajouté
dans cette phase.

## Budgets SQL couverts par les tests

| Endpoint | 1 objet | 10 objets | Budget |
|---|---:|---:|---:|
| Produits liste paginée | ≤5 | ≤6 | 6 |
| Produit détail | ≤4 | relations multiples : ≤4 | 4 |
| Commandes liste paginée | ≤3 | ≤3 | 3 |
| Commande détail | stable avec plus de lignes | stable | 3 environ |
| Médias liste paginée | stable | stable | 2 |
| Paiements liste paginée | ≤2 | ≤2 | 2 |

Le test direct du serializer produit vérifie également qu’après évaluation du
queryset préchargé, la sérialisation de cinq produits exécute zéro requête.

## Administration et configuration

Les listes d’administration utilisent `list_select_related`; l’administration
des commandes précharge aussi les lignes utilisées par le total.

Variables :

```text
API_DEFAULT_PAGE_SIZE=20
API_MAX_PAGE_SIZE=100
API_MAX_SEARCH_LENGTH=100
```

Le parsing refuse les valeurs non numériques via `django-environ`, ainsi que
les valeurs non positives ou un maximum inférieur à la valeur par défaut.

## Limites

Redis/cache distribué, CDN, APM, recherche full-text, `pg_trgm`, pagination
sans `COUNT(*)`, tests de charge et monitoring de production ne sont pas
intégrés. Le coût du `COUNT(*)` devra être réévalué à très grande échelle.
Les filtres SQL simples devront être remesurés avec un volume réaliste avant
tout nouvel index. Le paiement réel reste différé.
