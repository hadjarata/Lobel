# Phase 7 — Authentification et sécurité des comptes

## Audit et décision de modèle

LobelStore utilise `django.contrib.auth.User`; `AUTH_USER_MODEL` n'est pas
redéfini. Le profil `users.Customer` existe depuis `users.0001` et référence le
modèle substituable. Les commandes référencent le profil client en `SET_NULL`,
et l'historique de statut référence aussi l'utilisateur en `SET_NULL`.

Un remplacement tardif du modèle utilisateur n'a pas été effectué. Il
affecterait les migrations historiques, permissions, sessions, JWT, profils,
commandes et données existantes. Les protections sont donc ajoutées au profil
`Customer`, sans suppression ni fusion.

Audit de la base avant migration : 9 utilisateurs, 0 e-mail nul, 0 e-mail
vide, 0 doublon après `lower(trim(email))`.

## États du compte

- `User.is_active` : capacité technique Django, jamais modifiée par activation
  ou reset.
- `Customer.email_verified_at` : preuve de possession de l'adresse.
- `Customer.suspended_at` et `suspension_reason` : décision administrative.
- `Customer.token_version` : révocation immédiate des JWT existants.

La connexion exige les trois conditions : utilisateur actif, e-mail vérifié et
absence de suspension. L'activation ne modifie que `email_verified_at`. Le
reset ne modifie aucun état et une suspension n'est levée que par
`unsuspend_user()`.

```text
Création -> e-mail non vérifié -> e-mail vérifié -> authentification
                                  |
                                  +-> suspension -> reset (toujours suspendu)
                                                -> réactivation administrative
```

Les comptes antérieurs actifs sont marqués vérifiés par migration afin de ne
pas couper leurs accès existants.

## Mots de passe

L'inscription, le reset et le changement authentifié appellent
`validate_password()` avec le contexte utilisateur. Les validateurs Django
actifs couvrent similarité, longueur minimale de 10 caractères, mots de passe
communs et valeurs entièrement numériques. Les créations Django/admin
continuent d'utiliser les formulaires natifs et `set_password()`.

## JWT, logout et révocation

| Paramètre | Politique |
|---|---|
| Access | 15 minutes (`JWT_ACCESS_MINUTES`) |
| Refresh | 7 jours (`JWT_REFRESH_DAYS`) |
| Rotation | activée |
| Blacklist après rotation | activée |
| Algorithme | HS256, clé Django `SECRET_KEY` |
| En-tête | `Bearer` |
| Claim ajouté | `token_version` |

`POST /api/auth/logout/` accepte `{"refresh": "..."}`, blackliste le refresh
et répond `204`, y compris lors d'un second appel contrôlé. Un access token
n'est pas stocké : sa version est néanmoins comparée au profil à chaque
requête, ce qui permet sa révocation lors d'une suspension ou d'un changement
de mot de passe.

La suspension, le changement et le reset blacklistent tous les refresh
`OutstandingToken` et incrémentent `token_version`. Le refresh vérifie de
nouveau l'état actuel du compte.

## Throttling

| Endpoint | Scope | Taux |
|---|---|---|
| Inscription | `register` | 10/heure |
| Login | `login` | 10/minute |
| Refresh | `token_refresh` | 30/heure |
| Logout | `logout` | 30/heure |
| Reset demande (IP) | `password_reset_request` | 5/heure |
| Reset demande (e-mail normalisé) | `password_reset_request_email` | 5/heure |
| Reset confirmation | `password_reset_confirm` | 10/heure |
| Activation | `email_activation` | 10/heure |
| Changement mot de passe | `password_change` | 10/heure |

`DRF_NUM_PROXIES=0` est la valeur sûre par défaut. Elle ne doit être augmentée
que si la chaîne de reverse proxies et la réécriture de `X-Forwarded-For` sont
contrôlées.

## Reset et anti-énumération

La demande renvoie toujours le même statut, message et schéma pour une adresse
connue ou inconnue. Aucun UID ni token n'est renvoyé par l'API. Le token Django
est lié à l'utilisateur, expire selon `PASSWORD_RESET_TIMEOUT` et devient
invalide après changement du mot de passe. L'URL est envoyée via le backend
e-mail configuré et `FRONTEND_RESET_PASSWORD_URL`.

## Normalisation et unicité des e-mails

Les espaces extérieurs sont retirés, le domaine est mis en minuscules et les
comparaisons sont insensibles à la casse. Les points et alias `+` ne sont pas
transformés. La migration `users.0004` :

1. recherche les doublons `lower(trim(email))`;
2. échoue explicitement s'il en existe, sans fusion ni suppression;
3. crée l'index PostgreSQL unique partiel `unique_auth_user_email_ci`.

La validation API traduit aussi les conflits de concurrence en erreur DRF.

## Administration et conservation

L'administration du profil interdit toujours la suppression et propose les
actions Suspendre, Réactiver et Révoquer les sessions. Elles utilisent les
services métier. Aucune commande ni aucun paiement n'est modifié.

## Limites

L'envoi e-mail de production, MFA, sessions par appareil, interface de gestion
des sessions, CAPTCHA, détection avancée d'attaques et rotation automatique de
clé JWT ne sont pas intégrés. La migration vers un modèle utilisateur
personnalisé reste un chantier séparé. Le paiement réel reste différé.
