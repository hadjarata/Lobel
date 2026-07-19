import { useReducedMotion } from 'framer-motion';
import { springSnappy } from './motion';

/** Retourne une transition instantanée si l'utilisateur préfère moins d'animations. */
export function useMotionTransition(spring = springSnappy) {
  const reduced = useReducedMotion();
  return reduced ? { duration: 0 } : spring;
}
