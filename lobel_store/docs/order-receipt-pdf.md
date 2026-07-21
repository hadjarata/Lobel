# Justificatif de commande PDF

## Nature et émission

Le document est un justificatif de commande et de paiement, pas une facture
fiscale certifiée. Il est attribué par le backend lorsque la transition vers
`paid` valide un paiement `completed`, son montant, sa devise et les snapshots de
checkout. Les statuts postérieurs de préparation, livraison et remboursement
conservent le justificatif historique.

## Snapshot, numéro et idempotence

`OrderReceipt` possède une relation `OneToOne` protégée avec la commande. Son
snapshot JSON copie uniquement les champs commerciaux déjà figés de `Order` et
`OrderItem`, ainsi que la référence publique du paiement. Le catalogue n'est
jamais relu pour le rendu.

Le numéro `LOBEL-RCPT-AAAA-NNNNNN` est dérivé de la clé primaire créée par la
base, jamais de `count()`. La contrainte `OneToOne` et l'unicité du numéro
empêchent les doublons. Le modèle interdit la modification et la suppression des
données documentaires.

## Moteur et rendu

ReportLab génère le PDF A4 à la demande, sans fichier persistant ni ressource
distante. La police libre Bitstream Vera incluse avec ReportLab prend en charge
les accents français. Les tableaux répètent leur en-tête sur les pages
supplémentaires et le pied de page indique le numéro de page.

Les informations commerciales viennent de `STORE_DISPLAY_NAME`,
`STORE_LEGAL_NAME`, `STORE_CONTACT_EMAIL`, `STORE_CONTACT_PHONE` et
`STORE_ADDRESS`. Le logo est un monogramme vectoriel local, sans téléchargement.

## Endpoint et sécurité

`GET /api/orders/orders/{id}/receipt/` exige l'authentification et applique le
filtrage propriétaire existant. Une commande inaccessible retourne `404`; une
commande impayée retourne `409`.

Une réponse valide utilise :

- `Content-Type: application/pdf`;
- un nom de fichier backend limité au numéro du justificatif;
- `Cache-Control: private, no-store`;
- `X-Content-Type-Options: nosniff`.

Le PDF ne contient ni payload fournisseur, ni token, secret, URL publique,
donnée de carte, JavaScript ou pièce jointe. Une erreur de rendu retourne une
erreur neutre et ne modifie ni paiement, ni commande, ni stock.

## Frontend et diagnostic

React télécharge le Blob depuis l'endpoint authentifié, refuse un type MIME autre
que PDF, limite le nom de fichier à des caractères sûrs et révoque toujours
l'URL Blob. Il ne reconstruit ni ne persiste le document.

Pour diagnostiquer :

1. vérifier que le paiement est `completed` et la commande payée;
2. vérifier l'existence de `OrderReceipt`;
3. exécuter `python manage.py test orders.tests_phase9`;
4. extraire le texte avec pypdf;
5. rendre les pages avec `pdftoppm` pour contrôler la mise en page.

Limite : le document reflète le paiement initial. En cas de remboursement
ultérieur, il reste une preuve historique et ne constitue ni un avoir ni une
facture fiscale.
