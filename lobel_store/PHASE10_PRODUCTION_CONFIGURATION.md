# Phase 10 — Configuration de production

## Résultat

La configuration Django est séparée en quatre modules :

- `lobel_store.settings.base` : réglages communs sans secret ni base par défaut ;
- `lobel_store.settings.development` : développement local explicite ;
- `lobel_store.settings.test` : tests isolés et reproductibles ;
- `lobel_store.settings.production` : production stricte et fermée par défaut.

`manage.py` utilise le développement, ou les tests pour la commande `test`.
WSGI et ASGI utilisent la production par défaut. En exploitation, définir malgré
tout explicitement `DJANGO_SETTINGS_MODULE=lobel_store.settings.production`.

## Démarrage fermé en cas d'erreur

Le module de production refuse de démarrer si une valeur critique est absente ou
dangereuse. Cela couvre notamment :

- clé Django absente, trop courte ou manifestement factice ;
- hôte absent, joker, URL complète ou hôte local ;
- configuration PostgreSQL incomplète ou connexion sans TLS ;
- origine CORS/CSRF absente, non HTTPS, locale ou avec joker ;
- fournisseur de paiement simulé ou identifiants LigdiCash absents ;
- SMTP incomplet ;
- URL frontend non HTTPS ou locale ;
- stockage média local non déclaré persistant ;
- HSTS incohérent ou niveau de journalisation trop bavard.

Les contrôles applicatifs complémentaires sont dans `store/checks.py`.

## Variables de production

Toutes les valeurs sont injectées par l'environnement ou par le gestionnaire de
secrets de la plateforme. `.env.example` documente le format attendu sans
contenir de secret réel.

| Domaine | Variables obligatoires ou principales |
| --- | --- |
| Django | `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` |
| PostgreSQL | `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_SSLMODE` |
| Origines | `DJANGO_CORS_ALLOWED_ORIGINS`, `DJANGO_CSRF_TRUSTED_ORIGINS` |
| HTTPS | `DJANGO_SECURE_HSTS_SECONDS`, `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_SECURE_HSTS_PRELOAD` |
| Proxy | `DJANGO_USE_X_FORWARDED_PROTO`, `DJANGO_USE_X_FORWARDED_HOST` |
| Email | `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL` |
| Frontend | `FRONTEND_BASE_URL`, `PASSWORD_RESET_FRONTEND_URL`, `EMAIL_VERIFICATION_FRONTEND_URL` |
| Paiement | `PAYMENT_PROVIDER=ligdicash` et toutes les variables `LIGDICASH_*` |
| Médias | `MEDIA_STORAGE_BACKEND=local`, `MEDIA_LOCAL_STORAGE_IS_PERSISTENT=true`, `MEDIA_PERSISTENT_ROOT` |
| Logs/API | `DJANGO_LOG_LEVEL`, `ENABLE_API_DOCS`, `DJANGO_ADMIN_PATH` |

Les listes sont séparées par des virgules. Ne pas entourer les valeurs de
guillemets dans l'interface de la plateforme sauf si celle-ci les retire.

## Sécurité HTTP

La production active la redirection HTTPS, les cookies session et CSRF
`Secure`, `HttpOnly` pour la session, `SameSite=Lax`, `nosniff`, une politique
de référent stricte, `X-Frame-Options: DENY` et HSTS.

Activer `DJANGO_SECURE_HSTS_PRELOAD=true` seulement après avoir confirmé que le
domaine et tous ses sous-domaines sont durablement servis en HTTPS. Le profil de
CI l'active afin que `check --deploy` soit strictement sans avertissement.

Si TLS est terminé par un reverse proxy, celui-ci doit supprimer tout en-tête
entrant forgé et fournir `X-Forwarded-Proto: https`. Exemple Nginx :

```nginx
location / {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass http://django;
}
```

Ne jamais activer la confiance envers les en-têtes forwarded sans proxy de
confiance placé devant Django.

## Base de données, fichiers et sauvegardes

La production exige PostgreSQL avec TLS (`require`, `verify-ca` ou
`verify-full`). Pour une validation complète du certificat, préférer
`verify-full` et configurer les certificats PostgreSQL au niveau de la
plateforme.

Les fichiers statiques utilisent
`ManifestStaticFilesStorage` et sont produits avec `collectstatic`.
L'application ne sert pas les médias en production. Le seul backend média
installé est local : son chemin doit donc être monté sur un volume persistant,
partagé entre toutes les instances qui traitent les uploads, sauvegardé et
restauré régulièrement. Une plateforme à disque éphémère nécessite
l'intégration préalable d'un stockage objet ; ne pas contourner le contrôle de
persistance.

Les sauvegardes PostgreSQL et média restent une responsabilité d'exploitation.
Tester périodiquement leur restauration.

## Email, paiements et documentation API

La production utilise exclusivement SMTP ; le backend console n'est jamais
sélectionné. TLS et SSL sont mutuellement exclusifs.

Le fournisseur simulé est interdit. LigdiCash doit être entièrement configuré.
La confirmation distante n'étant pas encore implémentée dans le provider
installé, le code conserve volontairement un comportement fermé avant toute
livraison automatique. Cette intégration doit être terminée et testée avec les
webhooks réels avant ouverture commerciale.

Swagger/ReDoc sont désactivés par défaut en production avec
`ENABLE_API_DOCS=false`. Si une exposition temporaire est nécessaire, la
protéger au niveau réseau et la désactiver ensuite.

## Processus et journalisation

Le `Procfile` lance Gunicorn avec `gunicorn.conf.py`. Installer les dépendances
depuis `requirements.txt` dans une image Linux ; Gunicorn n'est pas destiné au
serveur de développement Windows.

Les logs vont sur stdout/stderr, sans fichier local et sans secret volontaire.
Les niveaux autorisés en production sont `INFO`, `WARNING`, `ERROR` et
`CRITICAL`. La collecte, la rétention, les alertes et la suppression des données
sensibles doivent être configurées sur la plateforme.

## Déploiement

Ordre conseillé :

```text
python -m pip install -r requirements.txt
python manage.py check
python manage.py check --deploy
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn lobel_store.wsgi:application --config gunicorn.conf.py
```

Avant mise en ligne :

1. créer et injecter de nouveaux secrets ;
2. vérifier DNS, certificat TLS, proxy et origines exactes ;
3. provisionner PostgreSQL TLS, volume média persistant et sauvegardes ;
4. valider SMTP et les emails transactionnels ;
5. valider LigdiCash et ses URLs de retour/callback ;
6. exécuter la CI et `check --deploy` sans avertissement ;
7. tester connexion, catalogue, upload, commande et paiement sur le staging ;
8. vérifier logs, métriques et alertes.

## Rotation de secrets

L'audit a trouvé dans l'ancien fichier de réglages des valeurs de repli
versionnées pour la clé Django et le mot de passe PostgreSQL. Elles ont été
supprimées des chemins de production. Il faut néanmoins les considérer comme
compromises : faire tourner la clé Django, le mot de passe PostgreSQL et tout
secret ayant réutilisé ces valeurs, puis invalider les sessions/JWT concernés.
Nettoyer l'historique Git seulement avec une procédure coordonnée, car sa
réécriture affecte tous les clones.

## Retour arrière

Conserver l'image applicative et la configuration de la version précédente.
Pour revenir en arrière, restaurer l'image, ses variables compatibles et, si une
migration destructive devait un jour être ajoutée, restaurer la sauvegarde
PostgreSQL correspondante. Cette phase n'ajoute aucune migration. Ne jamais
revenir à l'ancien fichier de réglages contenant les valeurs de repli.
