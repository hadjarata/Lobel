# Phase 8 — Sécurité des médias

## Audit initial

Le catalogue utilisait `ProductMedia.file`, champ générique image/vidéo sans
validation, et les champs `Collection.image` / `Collection.video`. Les chemins
reprenaient le nom client, sans limite de taille, dimensions, durée ou quota.
Les serializers de collection acceptaient directement les fichiers. Les
écritures catalogue étaient réservées à `is_staff`, sans permission média
explicite.

La base contenait 11 médias produit (10 images et 1 vidéo) et 3 images de
collection. Le dry-run a retrouvé les 14 fichiers : 13 images sont valides ;
la vidéo n'a pas pu être validée car FFprobe n'est pas installé. Aucun fichier
n'a été déplacé, modifié ou supprimé. Aucun média n'est présent dans l'index
Git. `media/` était déjà ignoré et `uploads/` l'est désormais aussi.

## Architecture

Le modèle existant est conservé pour éviter une migration destructive.
`media_type` sélectionne une politique serveur stricte, jamais une validation
client. `ProductMedia` stocke désormais format, MIME détecté, taille,
dimensions, durée, SHA-256 et état actif.

Les nouveaux uploads utilisent :

- `ProductMediaCreateSerializer` et `ProductMediaUpdateSerializer`;
- `CatalogMediaService` pour validation, verrouillage, quotas et stockage;
- `ProductMediaViewSet`, exclusivement multipart/form-data;
- l'abstraction Django Storage, sans accès métier direct à `MEDIA_ROOT`.

## Permissions

| Action | Anonyme | Client | Personnel sans permission | Gestionnaire autorisé |
|---|---:|---:|---:|---:|
| Lecture catalogue/médias actifs | Oui | Oui | Oui | Oui |
| Écriture catalogue sans média | Non | Non | Oui | Oui |
| Ajouter/remplacer une image | Non | Non | Non | Oui |
| Ajouter/remplacer une vidéo | Non | Non | Non | Oui |
| Archiver un média | Non | Non | Non | Oui |

Une écriture média requiert `is_staff` et la permission Django
`products.add_productmedia` ou `products.change_productmedia`. Les superusers
les possèdent implicitement.

## Politiques

| Type | Formats | Taille max | Dimensions/durée | Quota actif |
|---|---|---:|---|---:|
| Image | JPEG, PNG, WebP | 5 Mio | 8000×8000, 40 Mpx | 10/produit |
| Vidéo | MP4/H.264 | 50 Mio | 1920×1080, 120 s | 2/produit |

### Images

Pillow ouvre, vérifie, rouvre et décode réellement chaque image. Le format
détecté doit appartenir à l'allowlist et correspondre à l'extension. Le MIME
HTTP n'est pas utilisé comme preuve. SVG, GIF, XML, exécutables renommés,
images tronquées et formats non autorisés sont refusés. Le curseur est remis à
zéro. Les métadonnées EXIF ne sont pas encore supprimées : un réencodage
asynchrone contrôlé reste recommandé.

### Vidéos

FFprobe est exécuté sans shell, avec arguments séparés, JSON, fichier
temporaire et timeout. Il vérifie le conteneur ISO-BMFF, exactement une piste
vidéo, le codec H.264, le nombre total de pistes, la durée et la résolution.
En l'absence de FFprobe, les nouveaux uploads vidéo sont refusés. La vidéo
historique est conservée mais signalée par l'audit.

## Noms, stockage et cycle de vie

Les noms physiques sont des UUID serveur :

```text
products/{product_id}/media/{uuid}.png
collections/{id}/images/{uuid}.jpg
collections/{id}/videos/{uuid}.mp4
```

Le nom client, les séparateurs, chemins absolus et séquences `..` ne contrôlent
jamais le chemin final. L'extension canonique vient du contenu validé.

Les quotas comptent uniquement les médias actifs et sont vérifiés dans une
transaction après verrouillage PostgreSQL du produit. Le scope
`catalog_media_upload` autorise 30 requêtes/heure.

Lors du remplacement d'un `ProductMedia`, le nouveau fichier est validé et
sauvegardé avant que l'ancien soit supprimé via `transaction.on_commit()`.
L'archivage ne supprime aucun fichier. Pour les collections, les anciens
fichiers remplacés sont conservés et peuvent être signalés comme orphelins
plutôt que supprimés prématurément.

## Configuration

Le stockage local est prévu pour le développement. En production,
`media.W001` avertit si le stockage local est sélectionné sans persistance
explicitement organisée. Un backend objet doit être installé avant de choisir
une autre valeur ; aucune fausse intégration cloud n'est fournie.

Les limites sont configurables dans `.env.example`. Le reverse proxy ou load
balancer doit appliquer une limite de corps cohérente avec les 50 Mio vidéo.

## Administration et migration

L'administration affiche les métadonnées calculées en lecture seule, interdit
la suppression physique et applique les validateurs du modèle. Les quotas sont
aussi vérifiés dans le formulaire. Les uploads inline non contrôlés ont été
retirés.

La migration `products.0008` ajoute uniquement les métadonnées, l'archivage et
les fonctions de chemins sûrs. Les anciens chemins sont conservés et les
métadonnées inconnues restent vides ou `NULL`.

La commande suivante audite sans supprimer :

```powershell
python manage.py audit_catalog_media --dry-run
```

## Limites

Antivirus, analyse asynchrone, transcodage, miniatures, CDN, fournisseur cloud,
suppression automatique d'orphelins, modération de contenu, URLs signées,
sauvegarde externe et retrait EXIF ne sont pas intégrés. La détection des
polyglottes n'est pas garantie sans sandbox/antivirus. Le paiement réel reste
différé.
