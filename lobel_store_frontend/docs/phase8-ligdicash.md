# Phase 8 — Paiement LigdiCash

## 1. Diagnostic initial

Le projet possédait déjà un provider HTTP LigdiCash, les routes de création et
de callback, ainsi qu’un mock local. L’ancien endpoint partait toutefois du
panier, acceptait une origine frontend, créait plusieurs paiements possibles et
exposait le token de session dans le serializer. Le callback était désactivé en
production parce que la confirmation LigdiCash ne validait ni montant ni
référence.

## 2. Contrat LigdiCash réel

Le contrat retenu est le payin hébergé :

- `POST /pay/v01/redirect/checkout-invoice/create`;
- en-têtes `Apikey` et `Authorization: Bearer`;
- montant entier en XOF;
- URL de paiement dans `response_text`;
- token de création à stocker exclusivement côté serveur;
- `GET /pay/v01/redirect/checkout-invoice/confirm?invoiceToken=…`;
- statuts `pending`, `completed` et `notcompleted`;
- callback JSON et form-urlencoded, envoyé deux fois par événement.

LigdiCash ne documente pas une signature de callback. L’authenticité est donc
établie en ignorant le statut reçu et en appelant `confirm` avec le token stocké.
Il n’existe pas de sandbox isolée : l’équipe LigdiCash fournit un compte
d’intégration temporaire réel. Une transaction `pending` n’expire pas
automatiquement.

Sources officielles :

- https://developers.ligdicash.com/reference/endpoints/payin-redirect-create
- https://developers.ligdicash.com/reference/endpoints/payin-redirect-confirm
- https://developers.ligdicash.com/api-paiement/callback/securisation
- https://developers.ligdicash.com/concepts/cycle-vie-transaction
- https://developers.ligdicash.com/concepts/environnements

## 3. Architecture backend

`LigdicashProvider` est le seul client HTTP. `PaymentLifecycleService` contrôle
admissibilité, verrouillage, idempotence, création, URL, rafraîchissement et
transition. `PaymentService` synchronise la commande et consomme le stock via le
service de cycle de commande. `PaymentWebhookService` déduplique, retrouve le
paiement par `custom_data`, puis confirme côté LigdiCash.

`PaymentAuditEvent` est append-only. `reconcile_payments` relit manuellement les
transactions actives anciennes sans introduire Celery.

## 4. Architecture frontend

La dernière étape du checkout initialise le paiement avec `order_id` et une clé
stable, jamais avec un montant. L’adaptateur n’accepte que HTTPS sur
`app.ligdicash.com` — ou localhost pour le mock explicitement autorisé.
L’identifiant interne du paiement est mémorisé, jamais le token fournisseur.

La route `/checkout/payment/return` nettoie immédiatement l’URL, ignore tous les
paramètres, relit le paiement authentifié puis effectue un polling exponentiel
borné. Succès uniquement si paiement `completed` et commande `paid`.

## 5. Configuration

Variables backend :

```text
PAYMENT_PROVIDER
LIGDICASH_ENVIRONMENT
LIGDICASH_API_KEY
LIGDICASH_API_TOKEN
LIGDICASH_BASE_URL
LIGDICASH_STORE_NAME
LIGDICASH_STORE_URL
LIGDICASH_RETURN_URL
LIGDICASH_CANCEL_URL
LIGDICASH_CALLBACK_URL
LIGDICASH_HTTP_TIMEOUT
LIGDICASH_VERIFY_TLS
LIGDICASH_ALLOWED_CHECKOUT_HOSTS
```

Production exige provider et environnement `production`, HTTPS public, TLS,
timeout positif et hôte officiel. Le frontend ne reçoit aucune de ces clés.

## 6. Modèle et statuts

`Payment` ajoute UUID, référence marchande opaque, clé et empreinte
d’idempotence, statut fournisseur, URL temporaire, dates du cycle, échec,
dernière vérification et payload minimisé. Le token n’est jamais sérialisé.

Statuts internes : `created`, `initializing`, `pending`, `redirect_required`,
`processing`, `completed`, `failed`, `cancelled`, `expired`, `unknown`.
`completed` seul peut conduire la commande de `pending_payment` à `paid`.

## 7. Initialisation

`POST /api/payments/checkout/` accepte uniquement `order_id`; la clé est dans
`Idempotency-Key`. Le service verrouille la commande, vérifie ownership,
snapshot, statut, montant positif et devise XOF. Montant et lignes viennent du
snapshot. La référence `LOBEL-{UUID}` ne contient aucune donnée personnelle.

Même clé : même paiement. Nouvelle clé avec paiement actif : paiement actif
réutilisé. Communication ambiguë : statut `unknown`, aucune création aveugle.
Rejet explicite : `failed`. L’URL externe est validée avant exposition.

## 8. Callback et confirmation

Le callback est public, sans session ni CORS, accepte JSON/form, calcule une
empreinte et crée un reçu unique. Le statut et le token du callback sont ignorés.
Le serveur appelle `confirm` avec son token, vérifie statut, montant XOF et
référence marchande, puis exécute la transition atomique. Les doublons et
callbacks hors ordre ne consomment jamais deux fois le stock.

## 9. Retour frontend

Les query strings `success`, `status`, `amount`, identifiants et tokens sont
ignorées puis supprimées. La page affiche vérification, traitement, succès,
échec, annulation, expiration, réseau ou inconnu. Le polling s’arrête au statut
final, après huit essais, au démontage ou lorsque l’onglet est caché. Une
vérification manuelle reste disponible.

## 10. Sécurité

- Aucun secret ou token LigdiCash dans le frontend, stockage ou serializer.
- Aucun montant/devise frontend pris comme vérité.
- URL limitée au domaine LigdiCash attendu.
- Retour navigateur non autoritatif.
- Callback confirmé via appel serveur authentifié.
- Paiements filtrés par propriétaire.
- POST sensibles avec `skipAuthRefresh`.
- Logs limités aux identifiants internes, sans credentials ni données client.

## 11. Modifications par fichier

Backend :

- `payments/models.py`, migration `0010` : cycle, idempotence et audit.
- `providers/ligdicash.py` : payload snapshot, timeout, TLS et confirmation.
- `services/payment_lifecycle_service.py` : orchestration métier.
- `services/webhook_service.py` : re-vérification de production.
- `views.py`, `serializers.py`, `checks.py` : API sûre et configuration.
- `management/commands/reconcile_payments.py` : réconciliation.
- `admin.py` : lecture seule des événements.
- settings et `.env.example` : variables strictes.

Frontend :

- `api/payments.js`, contrats et endpoints : initialisation/refresh.
- `Checkout.jsx` : action de paiement fiable.
- `CheckoutSuccess.jsx` : retour et polling non autoritatifs.
- `payments/paymentPolicy.js` et tests : URL, statuts et backoff.
- `pendingCheckout.js` : suppression du token persistant.

## 12. Tests

Les tests backend couvrent montant serveur, ownership, commande non payable,
idempotence, paiement actif, URLs hostiles, pending, confirmation, consommation
unique du stock, audit et champs publics. Les tests historiques de provider,
callback, mock et permissions restent actifs.

La suite paiement frontend contient au moins 64 scénarios : protocoles et
domaines hostiles, cohérence de session, statuts, polling, paramètres retour et
absence de token. Aucun test ne contacte LigdiCash.

Playwright n’est pas installé; aucun E2E navigateur réel n’est exécuté.

## 13. CI

La CI exécute `test:payments`, toutes les suites frontend, le build production,
l’audit npm, Django/PostgreSQL, les settings de production et les tests réseau
mockés. Les valeurs CI sont factices et aucun appel extérieur n’est effectué.

## 14. Résultats des commandes

- migrations locales : `orders.0009`, `orders.0010` et `payments.0010` appliquées;
- Django check, check deploy et migrations sèches : réussis;
- backend Django/PostgreSQL : 206/206;
- frontend environnement : 10/10;
- auth : 56/56; contrats : 50/50; catalogue : 70/70;
- panier : 86/86; checkout : 5/5;
- paiements : 120/120, dont 70 scénarios dédiés Phase 8;
- frontend complet : 337/337;
- ESLint, build production et `npm audit` : réussis, zéro vulnérabilité;
- OpenAPI régénéré et réconciliation dry-run réussie;
- bundle sans credential LigdiCash ni source map.

Vite conserve l’avertissement non bloquant historique du chunk principal
supérieur à 500 kB.

## 15. Validation manuelle et compte d’intégration

La validation locale utilise le provider mock et les doubles HTTP. Aucun
credential de compte d’intégration LigdiCash n’est disponible dans le dépôt;
aucune transaction réelle n’a donc été initiée. La validation réelle devra être
réalisée avec le compte temporaire fourni par l’équipe LigdiCash.

## 16. Observabilité et runbook

Les événements `initialization_requested`, `initialization_succeeded`,
`initialization_ambiguous`, `initialization_failed`, `status_checked`,
`payment_confirmed` et `payment_failed` sont persistés. Les logs structurés
contiennent paiement, commande et transition. La commande de réconciliation
fournit nombre examiné et statut sans révéler de token.

Voir `docs/phase8-payment-runbook.md`.

## 17. Problèmes non corrigés

Remboursements complets, rapprochement bancaire, comptabilité, back-office
financier, notifications avancées, autres prestataires, application mobile,
optimisation générale et test réel de production restent hors périmètre.

## 18. Vérification du périmètre

Aucun remboursement automatique. Aucun secret frontend. Aucun statut payé
défini par le navigateur. Aucun montant client autoritatif. Aucune confiance
dans le retour. Aucun paiement réel en CI. Permissions, JWT, panier et checkout
sont conservés.

## 19. Verdict

L’intégration est prête pour une validation complète avec le compte
d’intégration LigdiCash, puis un staging contrôlé après réussite des callbacks,
confirmations et scénarios opérateur.
