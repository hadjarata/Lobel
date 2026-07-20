import { motion as Motion } from 'framer-motion';
import { pageVariants, springSnappy } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';

const PageTransition = ({ children }) => {
  const transition = useMotionTransition(springSnappy);

  return (
    <Motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={transition}
      style={{ width: '100%' }}
    >
      {children}
    </Motion.div>
  );
};

export default PageTransition;
