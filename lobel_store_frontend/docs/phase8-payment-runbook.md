# Runbook incidents paiement

Ne jamais modifier directement un statut de paiement ou de commande en base.
Conserver les preuves, utiliser `confirm` et les services métier.

| Incident | Diagnostic | Action sûre | Action interdite | Escalade |
|---|---|---|---|---|
| LigdiCash indisponible | logs `provider_communication_error`, état `unknown` | conserver la clé, attendre, réconcilier | recréer en boucle | support LigdiCash |
| Callback absent | vérifier accessibilité HTTPS et `last_checked_at` | `reconcile_payments --payment-id ID` | marquer payé | exploitation puis LigdiCash |
| Pending long | `confirm`, audit, dashboard | laisser pending et réconcilier | expirer automatiquement | support après délai métier |
| Client débité, commande non payée | référence marchande et `confirm` | geler livraison, collecter preuve, réconcilier | payer/annuler manuellement | finance + LigdiCash |
| Montant incohérent | comparer commande/payment/confirm | bloquer traitement, conserver événement | corriger le montant en DB | sécurité + finance |
| Callback invalide | hash, référence, résultat confirm | répondre sans traiter | faire confiance au payload | sécurité |
| Secret compromis | audit accès et logs | régénérer dashboard, déployer, vérifier transactions | publier l’ancien secret | sécurité + LigdiCash |
| Double notification | reçu de déduplication | vérifier qu’un seul audit final existe | supprimer les preuves | développement si doublon traité |
| Confirmation tardive | statut précédent et stock | laisser le service idempotent décider | forcer une transition | métier + support |
| Panne pendant transition | transaction DB et audit | relancer `confirm`/réconciliation | SQL manuel | DBA + développement |
| Réconciliation en erreur | stderr sans secret, connectivité | relancer ciblé après correction | boucle non bornée | exploitation |

Commandes :

```bash
python manage.py reconcile_payments --dry-run --age-minutes 15
python manage.py reconcile_payments --payment-id 123
python manage.py reconcile_payments --age-minutes 30 --limit 100
```

Checklist production : credentials dédiés, URLs/DNS/certificat HTTPS, callback
public, firewall, rotation testée, validation d’intégration signée, mocks
désactivés, CSP/CORS revus, logs/alertes, réconciliation planifiée, sauvegarde,
support et rollback documentés.
