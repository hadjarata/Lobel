/** Transitions spring – rapides (~0.3s), sans animation décorative. */

export const springSnappy = {
  type: 'spring',
  stiffness: 420,
  damping: 32,
  mass: 0.85,
};

export const springModal = {
  type: 'spring',
  stiffness: 380,
  damping: 34,
  mass: 0.9,
};

export const springSheet = {
  type: 'spring',
  stiffness: 400,
  damping: 36,
  mass: 0.95,
};

export const springTap = {
  type: 'spring',
  stiffness: 500,
  damping: 28,
  mass: 0.6,
};

export const pageVariants = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
};

export const toastVariants = {
  initial: { opacity: 0, y: 12, scale: 0.98 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.98 },
};

export const backdropVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const sheetUpVariants = {
  initial: { y: '100%' },
  animate: { y: 0 },
  exit: { y: '100%' },
};

export const slideFromLeftVariants = {
  initial: { x: '-100%' },
  animate: { x: 0 },
  exit: { x: '-100%' },
};

export const panelVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -6 },
};

export const zoomModalVariants = {
  initial: { opacity: 0, scale: 0.96 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.98 },
};
