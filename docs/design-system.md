# LobelStore Design System — version 1

Cette version fournit une fondation globale additive. Elle ne demande pas de
réécrire les pages existantes : les nouveaux écrans utilisent les primitives
`src/components/ui`, puis les écrans historiques sont migrés progressivement.

## Principes

- Interface minimaliste, premium, en noir, blanc et gris neutres.
- L’image produit reste l’élément visuel principal.
- Les couleurs d’état sont réservées au retour fonctionnel.
- Utiliser un token avant d’ajouter une valeur CSS.
- Construire mobile-first aux seuils documentés.
- Conserver un focus visible au clavier et des libellés accessibles.
- Les mouvements sont courts, fonctionnels et facultatifs.

## Tokens

Les tokens sont définis dans `src/styles/tokens.css`.

### Couleurs

- Surfaces : `--color-background`, `--color-surface`,
  `--color-surface-subtle`.
- Texte : `--color-text`, `--color-text-muted`.
- Structure : `--color-border`, `--color-border-strong`.
- Action principale : `--color-accent`, `--color-accent-contrast`.
- États : `--color-success`, `--color-warning`, `--color-danger`.
- Focus : `--color-focus` et `--focus-ring`.

Les couleurs d’état ne doivent pas servir de décoration ou de couleur de
marque.

### Typographie

Utiliser `--font-family-sans` pour les textes et contrôles, et
`--font-family-serif` pour les grands titres éditoriaux. Les deux piles
prévoient des polices système de repli. L’échelle va de `--font-size-xs` à
`--font-size-2xl`, avec les graisses `regular`, `medium`, `semibold` et
les interlignes `tight`, `normal`, `relaxed`.

### Espacement, rayon et ombre

- Espacement : `--space-0` à `--space-9`.
- Rayon : `none`, `sm`, `md`, `lg`, `full`.
- Ombre : `none`, `sm`, `md`, `lg`.

`full` est réservé aux pastilles et formes circulaires. Les ombres servent à
exprimer une élévation réelle, pas à décorer toutes les cartes.

### Breakpoints

L’échelle de référence est :

| Nom | Valeur | Usage |
| --- | ---: | --- |
| `sm` | 30rem / 480px | grands mobiles |
| `md` | 48rem / 768px | tablettes |
| `lg` | 64rem / 1024px | bureau |
| `xl` | 75rem / 1200px | grand bureau |

Les variables `--breakpoint-*` documentent les valeurs, mais CSS ne permet
pas de les employer directement dans une condition `@media`. Les media
queries répètent donc les valeurs en `rem`.

### Mouvement

Les transitions CSS utilisent `--duration-fast`, `--duration-normal` ou
`--duration-slow` et `--ease-standard`. Framer Motion continue d’utiliser
`src/utils/motion.js` et `useMotionTransition`.

Avec `prefers-reduced-motion: reduce`, les durées deviennent instantanées et
les animations CSS globales sont neutralisées. Une animation ne doit jamais
être indispensable pour comprendre ou terminer une action.

## Accessibilité et focus

Le focus global utilise `:focus-visible`. Ne pas supprimer son outline sans
proposer un indicateur au moins équivalent. Chaque champ doit recevoir un
libellé visible, sauf justification accessible explicite.

## Primitives

Importer depuis `src/components/ui` :

```jsx
import {
  Badge,
  Button,
  Card,
  Container,
  Input,
  Section,
  Select,
  Textarea,
} from '../components/ui';
```

### Button

- Variantes : `primary`, `secondary`, `outline`.
- Tailles : `small`, `medium`, `large`, `xlarge`.
- États : `disabled` et `loading`.
- `gold` reste un alias de compatibilité pour les anciens appels, mais ne
  doit plus être introduit.
- Le type par défaut est `button`, afin d’éviter une soumission implicite.

```jsx
<Button variant="primary" loading={saving}>
  Enregistrer
</Button>
```

### Input, Textarea et Select

Ces composants conservent les attributs HTML natifs. Ils acceptent `label`,
`hint` et `error`. `error` ajoute automatiquement `aria-invalid`, une
description accessible et un message avec `role="alert"`.

```jsx
<Input
  label="E-mail"
  type="email"
  autoComplete="email"
  error={errors.email}
/>
```

### Badge

Variantes : `neutral`, `strong`, `success`, `warning`, `danger`. Employer un
badge pour un statut ou une information courte, jamais comme bouton.

### Card

`padded` est actif par défaut. `elevated` ajoute l’ombre d’élévation. La
propriété `as` permet de choisir un élément sémantique comme `article`.

### Container

Tailles : `default`, `narrow`, `wide`. Il gère largeur maximale, centrage et
gouttières responsive.

### Section

Tons recommandés : `default`, `subtle`, `inverse`. Les anciens noms `white`,
`beige` et `rose` restent acceptés comme alias. `align` vaut `center` par
défaut et peut valoir `start`. Un `id` génère une relation accessible entre
la section et son titre.

## Migration

Ne pas convertir une page entière uniquement pour adopter ces primitives.
Remplacer les éléments répétés lors d’une évolution fonctionnelle ou visuelle
de la zone concernée, en conservant ses états loading, empty, error, disabled
et ses comportements clavier.
