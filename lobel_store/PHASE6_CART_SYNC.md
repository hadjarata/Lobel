# Phase 6 backend — synchronisation panier

La fusion invitée utilise `POST /api/orders/orders/cart/merge/` avec le header
`Idempotency-Key`. Elle est partielle, transactionnelle et sérialisée par un
verrou sur le client. Les résultats sont mémorisés dans `CartMergeReceipt`.

`DELETE /api/orders/orders/cart/clear/` vide atomiquement un panier non figé.
`POST /api/products/products/resolve-variants/` résout au plus 50 variantes
publiquement afin de rafraîchir un panier invité sans charger le catalogue.

Le backend ignore tout champ de prix ou total supplémentaire et recalcule les
snapshots depuis la variante. Les codes principaux sont `invalid_quantity`,
`invalid_variant`, `inactive_variant`, `inactive_product`,
`insufficient_stock`, `cart_locked` et `idempotency_conflict`.
