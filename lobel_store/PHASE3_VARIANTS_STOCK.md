# Phase 3 — variantes, panier et stock

L’unité vendable et l’unité de stock sont désormais `ProductVariant`
(`produit + couleur + taille`). Une écriture publique de panier accepte
uniquement `variant_id` et `quantity`; le produit, le prix et les snapshots
sont déterminés côté serveur.

`MAX_CART_ITEM_QUANTITY` vaut 99. L’ajout au panier vérifie le stock mais ne le
réserve pas. Le checkout le revérifie sous verrou PostgreSQL, actualise les
snapshots de ligne, puis la confirmation de paiement verrouille et décrémente
exactement la variante concernée. Le verrou du paiement et le statut payé
conservent l’idempotence du workflow.

La base garantit un seul panier incomplet par client, une seule ligne par
variante et panier, une quantité positive, un stock non négatif et l’unicité
d’une combinaison produit/couleur/taille. Les anciennes lignes ne reçoivent une
variante que si le catalogue n’offre qu’une correspondance; les commandes
ambiguës restent lisibles grâce aux snapshots et ne sont pas attribuées
arbitrairement.

Les tests de concurrence sont des `TransactionTestCase` PostgreSQL avec
connexions distinctes, threads et barrières. Ils ne doivent pas être présentés
comme valides sous SQLite.
