# Service de robe sur mesure via WhatsApp

## Objectif et limites

La page d'accueil présente un unique service public de confection. Elle explique
quatre étapes dans un dialogue avant d'ouvrir WhatsApp. Il n'existe ni stockage de
mensurations, ni devis automatique, ni commande sur mesure, ni API WhatsApp.

## Administration et modèle

`CustomDressService` appartient à l'application `content`. Le titre, la description,
l'image, le numéro, le message, le libellé du bouton, la disponibilité, le délai de
réponse et la mention tarifaire sont administrables. Une contrainte en base et une
désactivation transactionnelle garantissent une seule configuration active.

Le numéro contient strictement 8 à 15 chiffres ASCII, indicatif pays inclus, sans
`+`, espace, tiret ou URL. Les ambiguïtés ne sont pas normalisées. Le message est
générique, limité à 1 000 caractères et refuse les balises HTML.

## Image

L'image est obligatoire. JPEG, PNG et WebP sont vérifiés d'après leur contenu avec
Pillow. La limite `CUSTOM_DRESS_MAX_IMAGE_SIZE_MB` vaut 5 Mo par défaut. Le stockage
emploie un nom UUID sous `content/custom-dress/`. En cas d'échec d'affichage, le
frontend conserve le contenu et affiche un fond sobre.

## API

`GET /api/content/custom-dress-service/` est public et en lecture seule. Il retourne
la configuration active, une URL d'image absolue et quatre étapes fixes. Il omet les
identifiants, dates et états internes. Sans configuration active, il retourne `204`.
Les réponses utilisent `Cache-Control: public, max-age=60`; les écritures retournent
`405`. Le schéma OpenAPI est généré par drf-yasg.

## Parcours, sécurité et confidentialité

Le premier bouton ouvre un `<dialog>` natif : focus initial, confinement natif,
fermeture avec Échap, bouton nommé et restauration du focus. Le dialogue reste
scrollable sur petit écran.

Le frontend construit exclusivement
`https://wa.me/{numero}?text={encodeURIComponent(message)}` et ouvre le lien avec
`target="_blank"` et `rel="noopener noreferrer"`. Aucun domaine, URL complète,
profil, nom, adresse, panier, commande, paiement, token ou mesure client n'est
injecté. Une erreur API ou une réponse `204` masque la section.

## Tests

Les tests Django couvrent les champs requis, les médias réels, la limite de taille,
le SVG, les numéros acceptés/refusés, le texte brut, l'activation unique, le contrat
public, le cache, le `204`, les méthodes refusées et l'admin. Les tests React
couvrent le rendu, l'image et son fallback, le dialogue, les étapes, le focus,
Échap, l'URL encodée, les attributs sûrs, les erreurs et le démontage.
