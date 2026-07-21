import { motion, useReducedMotion } from 'framer-motion';
import { springSnappy } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';

const MotionDiv = motion.div;

const HomeReveal = ({
  children,
  className = '',
  stagger = false,
  ...props
}) => {
  const reducedMotion = useReducedMotion();
  const revealTransition = useMotionTransition(springSnappy);
  const variants = {
    hidden: reducedMotion ? { opacity: 1 } : { opacity: 0, y: 18 },
    visible: {
      opacity: 1,
      y: 0,
      transition: reducedMotion
        ? { duration: 0 }
        : {
          ...revealTransition,
          ...(stagger ? { staggerChildren: 0.07, delayChildren: 0.04 } : {}),
        },
    },
  };

  return (
    <MotionDiv
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.12 }}
      {...props}
    >
      {children}
    </MotionDiv>
  );
};

export const HomeRevealItem = ({ children, className = '', ...props }) => {
  const reducedMotion = useReducedMotion();
  const revealTransition = useMotionTransition(springSnappy);
  return (
    <MotionDiv
      className={className}
      variants={{
        hidden: reducedMotion ? { opacity: 1 } : { opacity: 0, y: 12 },
        visible: {
          opacity: 1,
          y: 0,
          transition: reducedMotion
            ? { duration: 0 }
            : revealTransition,
        },
      }}
      {...props}
    >
      {children}
    </MotionDiv>
  );
};

export default HomeReveal;
