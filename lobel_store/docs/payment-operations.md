# Exploitation des paiements

Les commandes de maintenance sont idempotentes et doivent être planifiées par
l'infrastructure. Le dépôt fournit les commandes, mais un `Procfile` web seul ne
constitue pas un scheduler.

Planning recommandé (UTC) :

```cron
*/5 * * * * python manage.py reconcile_payments --age-minutes 5 --limit 200
*/5 * * * * python manage.py reconcile_refunds --limit 200
*/10 * * * * python manage.py expire_pending_orders --limit 500
*/10 * * * * python manage.py retry_order_notifications --failed-only --limit 500
*/5 * * * * python manage.py payment_health --window-minutes 60 --fail-on-alert
```

Chaque exécution doit avoir un timeout, capturer la sortie et déclencher une
alerte sur code de sortie non nul ou absence d'exécution. En environnement à
plusieurs instances, n'activer qu'un scheduler, ou utiliser les verrous de la
plateforme.

`payment_health` émet une ligne JSON exploitable par la collecte de logs :
taux d'échec d'initialisation, paiements `unknown`/`processing` anciens,
webhooks rejetés, doubles paiements, commandes à rembourser, incohérences de
montant/devise, échecs de stock après paiement, alertes critiques et délai
moyen de confirmation.

Une initialisation réseau ambiguë ne doit jamais créer automatiquement une
seconde session. La réconciliation appelle la recherche par référence
marchande si aucun token de session n'a été reçu. Le fournisseur retenu doit
donc documenter et implémenter cette opération.
