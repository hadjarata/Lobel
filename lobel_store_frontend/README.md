# LobelStore Frontend

Application React/Vite de LobelStore. La seule racine npm est le dossier
`lobel_store_frontend`.

Le paiement est initialisé uniquement depuis une commande `pending_payment`.
Le frontend n'envoie aucun montant et ne contient aucun secret LigdiCash. La
route `/checkout/payment/return` relit toujours le backend avant d'afficher un
succès. Voir `docs/phase8-ligdicash.md`.

## Commandes client

Les routes privées `/account/orders`, `/account/orders/:id` et
`/order-confirmation/:id` relisent les statuts depuis le backend et utilisent
les snapshots historiques. Aucune commande privée n'est persistée dans le
navigateur. Voir `docs/phase9-order-lifecycle.md`.

```bash
npm run test:orders
```

## Environnement technique

- Node.js recommandé : `22.17.0` (`.nvmrc`)
- Node.js compatible : `^20.19.0` ou `>=22.12.0`
- npm : `>=10.9.0`

```bash
nvm use
npm ci
```

## Modes

Quatre modes explicites sont acceptés :

- `development` : HTTP local autorisé, mock et logs de debug configurables ;
- `test` : URL factice explicite, aucun fallback vers un réseau réel ;
- `staging` : URL API HTTPS publique obligatoire, mock et debug interdits ;
- `production` : mêmes contraintes strictes que staging.

`VITE_APP_ENV`, lorsqu’il est fourni, doit correspondre au mode Vite.
Il est obligatoire en staging et production.

## Variables publiques

Toute variable `VITE_*` est intégrée au JavaScript envoyé au navigateur. Ne
jamais y placer de mot de passe, token, secret Django, clé privée ou clé secrète
LigdiCash.

| Variable | Rôle |
| --- | --- |
| `VITE_APP_ENV` | environnement applicatif explicite |
| `VITE_APP_NAME` | nom public, `LobelStore` par défaut |
| `VITE_API_BASE_URL` | URL absolue obligatoire de l’API |
| `VITE_DEV_BACKEND_TARGET` | cible optionnelle du proxy en développement |
| `VITE_ENABLE_PAYMENT_MOCK` | mock local ; interdit en staging/production |
| `VITE_ENABLE_DEBUG_LOGS` | logs techniques ; interdits en staging/production |

En staging et production, l’API doit utiliser HTTPS et ne peut pas cibler
localhost, une adresse loopback ou un domaine `.local`. Les identifiants dans
l’URL, fragments et paramètres de requête sont refusés.

## Commandes

```bash
npm run dev
npm run lint
npm run test:env
npm run test
npm run test:auth
npm run build:staging
npm run build:production
npm run build
npm run preview
```

`npm run build` est un alias strict de `build:production`. Il échoue si les
variables de production sont absentes. Exemple PowerShell :

```powershell
$env:VITE_APP_ENV='production'
$env:VITE_API_BASE_URL='https://api.example.com'
$env:VITE_ENABLE_PAYMENT_MOCK='false'
$env:VITE_ENABLE_DEBUG_LOGS='false'
npm.cmd run build
```

Une URL HTTP, locale, contenant des identifiants, ou un mock activé entraîne une
erreur avant que Vite ne génère `dist`.

## Politique de build

- le proxy `/api`, `/media`, `/swagger` et `/admin` existe uniquement en
  développement ;
- aucun fallback local n’existe en staging ou production ;
- les sourcemaps de build sont désactivées tant qu’aucun monitoring sécurisé
  n’est configuré ;
- `dist` est nettoyé avant chaque build ;
- le seuil d’avertissement des chunks reste fixé à 500 kB.

## Déploiement SPA

Le serveur statique doit renvoyer `index.html` pour toute route applicative
inconnue, notamment `/product/:id`, `/profile` et `/checkout`.

Exemples conceptuels :

- Nginx : `try_files $uri $uri/ /index.html;`
- Netlify : règle `/* /index.html 200`
- Vercel : rewrite `/(.*)` vers `/index.html`

Ne créer qu’une configuration réelle lorsque la plateforme d’hébergement aura
été choisie.

Les assets hashés peuvent être mis en cache longtemps avec `immutable`.
`index.html` doit être revalidé fréquemment.

## Headers attendus du serveur/CDN

Configurer au minimum :

- `Strict-Transport-Security` après validation HTTPS complète ;
- `X-Content-Type-Options: nosniff` ;
- `Referrer-Policy: strict-origin-when-cross-origin` ;
- une `Permissions-Policy` restrictive adaptée aux fonctions utilisées ;
- une CSP contenant notamment `frame-ancestors 'none'`.

La directive CSP `connect-src` doit autoriser l’API réelle ; `img-src` et
`media-src` doivent autoriser les domaines médias réellement utilisés. La CSP
finale doit être testée avec LigdiCash avant déploiement et ne doit pas être
copiée aveuglément.

## Limites restantes

Le frontend n’est pas encore prêt pour la production. Restent hors de cette
phase :

- migration future du refresh token vers un cookie `HttpOnly` ;
- contrats API, variantes, panier et pagination ;
- retour LigdiCash et mocks de fiche produit ;
- tests UI/E2E et CI fonctionnelle complète ;
- code splitting, chunk supérieur à 500 kB et optimisation des médias.

## Architecture d’authentification

Le client public traite login, inscription, refresh, vérification d’e-mail et
réinitialisation. Le client authentifié ajoute le header `Authorization` et ne
rejoue après renouvellement que les méthodes `GET`, `HEAD` et `OPTIONS`. Les
créations de commande, de paiement et toutes les autres mutations ne sont
jamais rejouées automatiquement.

L’access token reste uniquement en mémoire. Le refresh token est conservé dans
une entrée versionnée `lobelstore.auth.v1`, derrière `authStorage.js`. Cette
persistance permet de restaurer une session après rechargement, mais elle reste
accessible à du JavaScript exécuté dans la page et n’offre donc pas la
protection XSS d’un cookie `HttpOnly`.

Le backend actuel ne fournit pas de cookie de refresh. Une évolution future
devrait ajouter un cookie `Secure`, `HttpOnly` et `SameSite` avec une stratégie
CSRF adaptée, tout en préparant explicitement la compatibilité des clients
existants.

### Cycle de session

Au démarrage, une session persistée déclenche un refresh, puis le chargement de
`/api/users/customers/me/`. Une panne réseau termine l’écran d’initialisation
sans supprimer le refresh persistant ; une réponse `400`, `401` ou `403` du
refresh invalide définitivement la session.

Une promesse unique déduplique les refresh concurrents. La rotation remplace le
refresh atomiquement. Un compteur de génération empêche un refresh terminé
après logout de restaurer la session. Le logout local est toujours effectué,
même si `POST /api/auth/logout/` est indisponible.

L’expiration locale du JWT sert uniquement à anticiper le renouvellement
45 secondes avant `exp`. Les claims décodés ne servent jamais d’autorisation :
les permissions Django/DRF restent l’unique autorité.

### Diagnostic

```bash
npm run test:auth
npm test
npm run lint
```

Inspecter ensuite l’onglet Réseau sans copier de tokens dans un ticket ou un
journal. Les erreurs réseau ne doivent pas effacer une session restaurable.

## Contrats API

La matrice frontend/backend, les serializers consommés, les règles de
pagination, médias, montants et erreurs sont documentés dans
[`docs/frontend-api-contracts.md`](docs/frontend-api-contracts.md).

```bash
npm run test:contracts
```

## Panier et variantes

Le panier est centralisé dans `CartProvider`. Le panier invité persiste
uniquement des identifiants de variantes et quantités sous la clé versionnée
`lobelstore.guest-cart.v1`; prix, stock et montants sont rafraîchis par l'API.
Après connexion, la fusion est partielle, transactionnelle et idempotente.

```bash
npm run test:cart
```

Le contrat, la politique de conflit et les limites sont détaillés dans
[`docs/phase6-cart.md`](docs/phase6-cart.md).
