# Couverture minimale de l'accueil

## Configuration

HomeHero est une configuration unique contenant seulement :

- le titre ;
- la description ;
- le type de média IMAGE ou VIDEO ;
- une image ou une vidéo, exclusivement.

Le titre par défaut est « Bienvenue sur LobelStore ». La description par
défaut est « Découvrez notre sélection de créations et explorez notre
boutique. »

Il n'existe plus de surtitre, image mobile, poster, bouton administrable,
activation ou planification. Le bouton « Voir la boutique » et sa route
/shop sont statiques dans React.

## Médias

- images : JPEG, PNG ou WebP, 5 Mo par défaut ;
- vidéo : MP4 H.264 validée avec ffprobe, 25 Mo par défaut ;
- en mode image, image est obligatoire et video doit être vide ;
- en mode vidéo, video est obligatoire et image doit être vide.

Les limites restent configurées avec HOME_HERO_MAX_IMAGE_SIZE_MB et
HOME_HERO_MAX_VIDEO_SIZE_MB.

## Administration

L'administration affiche uniquement le contenu et le média. Dès qu'une
configuration existe, l'ajout d'une seconde est masqué. Une contrainte en
base protège également le singleton en dehors de l'admin.

## API

GET /api/content/home-hero/ est public et en lecture seule :

- 200 avec title, description, media_type et media_url ;
- 204 lorsqu'aucune configuration n'existe ;
- Cache-Control: public, max-age=60.

L'URL média est absolue. Aucun ancien champ ou état administratif n'est
exposé.

## Frontend

Le frontend utilise les textes par défaut tant que l'API ne fournit pas une
configuration valide. Une erreur de chargement du média conserve un fond
noir neutre, les textes et le lien statique vers /shop.

La vidéo est muette, en boucle et contrôlable. Avec
prefers-reduced-motion: reduce, elle n'est pas lancée et le fond neutre est
conservé.
