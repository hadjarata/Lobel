# LobelStore backend

## Paiement LigdiCash

Le backend est l’unique autorité pour le montant, la devise, la référence
marchande et l’état d’un paiement. Le frontend initialise un paiement à partir
d’une commande `pending_payment`, redirige vers l’URL hébergée validée, puis
interroge le backend au retour. Les paramètres de l’URL de retour ne constituent
jamais une preuve de paiement.

Variables requises : `LIGDICASH_ENVIRONMENT`, `LIGDICASH_API_KEY`,
`LIGDICASH_API_TOKEN`, `LIGDICASH_BASE_URL`, `LIGDICASH_CALLBACK_URL`,
`LIGDICASH_RETURN_URL`, `LIGDICASH_CANCEL_URL`, `LIGDICASH_HTTP_TIMEOUT`,
`LIGDICASH_VERIFY_TLS` et `LIGDICASH_ALLOWED_CHECKOUT_HOSTS`.

En production, les secrets manquants, les URL non HTTPS, la désactivation de
TLS et les hôtes de redirection non autorisés provoquent un arrêt explicite.

```bash
python manage.py migrate
python manage.py showmigrations orders payments
python manage.py check
python manage.py reconcile_payments --dry-run
```

Voir aussi `../lobel_store_frontend/docs/phase8-payment-runbook.md`.

## Cycle de commande

Les statuts passent uniquement par `OrderLifecycleService` :

```bash
python manage.py expire_pending_orders --dry-run
python manage.py retry_order_notifications --dry-run --failed-only
```

Les reçus HTML sont construits depuis les snapshots via un endpoint authentifié.
Voir `../lobel_store_frontend/docs/phase9-order-lifecycle.md`.
