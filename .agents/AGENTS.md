## LobelStore frontend design rules

All frontend changes must follow `docs/design-system.md`.

General direction:

- Minimalist, elegant and premium e-commerce interface.
- Black, white and neutral gray palette.
- Product imagery is the primary visual element.
- Do not introduce arbitrary colors, spacing, shadows or radii.
- Reuse existing design tokens and shared components.
- Do not duplicate reusable UI components inside pages.
- Design mobile-first, then validate tablet and desktop layouts.
- Preserve accessibility, keyboard navigation and visible focus states.
- Animations must be subtle, functional and respect reduced-motion.
- Do not modify business logic or API contracts during visual redesigns
  unless the task explicitly requires it.

Before finishing a UI task:

1. Run linting and tests.
2. Check the page at supported breakpoints.
3. Check loading, empty, error and disabled states.
4. Confirm that no hard-coded design values were introduced unnecessarily.
5. Summarize modified files and validation performed.