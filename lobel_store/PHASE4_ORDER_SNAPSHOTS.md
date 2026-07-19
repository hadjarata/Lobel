# Phase 4 — historique immuable des commandes

Le catalogue et le profil client sont des données vivantes. Après le checkout,
la source de vérité commerciale est exclusivement constituée des snapshots de
`Order` et `OrderItem`. `snapshot_at` marque le début de l’immutabilité.

## Données figées

Une ligne conserve les références numériques historiques du produit et de la
variante, leurs noms, la couleur, la taille, le SKU, le prix unitaire, la
quantité, la devise, la remise totale de ligne et son sous-total.

La commande conserve le nom et l’email du client, le destinataire, le téléphone,
l’adresse simple et le pays de livraison ainsi que le sous-total, les frais de
livraison, la remise de commande, le total et la devise canonique `XOF`.

## Formules

Tous les calculs utilisent `Decimal` et une quantification à deux décimales :

```text
brut ligne = prix unitaire × quantité
sous-total ligne = brut ligne − remise totale de ligne
total commande = sous-total commande + livraison − remise commande
```

Les remises et montants négatifs sont refusés. Aucun moteur de promotion ni
frais de livraison variables n’est introduit : ces deux valeurs valent
actuellement zéro, mais leur sémantique historique est définie.

## Cycle de vie

L’ajout au panier crée des snapshots préparatoires. Le checkout verrouille les
lignes et variantes, recalcule côté serveur, écrit tous les snapshots puis pose
`snapshot_at`. Les modifications ordinaires des lignes, montants et coordonnées
sont ensuite refusées par l’API, les services et les gardes de modèle.

Le paiement est créé avec `Order.total_amount` et `Order.currency`. La
confirmation vérifie encore ces valeurs et ne relit aucun prix catalogue.

Les clés étrangères vers `Product` et `ProductVariant` utilisent `SET_NULL`.
Une suppression physique conserve donc les lignes et leur lecture historique.

## Migration et limites

Le backfill préserve d’abord les snapshots Phase 3. Les identifiants de clés
étrangères sont copiés comme références historiques. Un sous-total n’est calculé
que si un prix de ligne existait déjà. Pour une commande finalisée, un paiement
confirmé est prioritaire pour le total; sinon seules les lignes entièrement
renseignées sont sommées. Les coordonnées du profil actuel sont une
approximation documentée lorsqu’aucun snapshot antérieur n’existait.

Certaines anciennes commandes peuvent donc garder des montants ou adresses
incomplets. Les promotions, la facturation PDF, l’audit administratif complet et
le paiement réel restent hors périmètre.
