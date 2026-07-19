import { motion } from 'framer-motion';
import { pageVariants, springSnappy } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';

const PageTransition = ({ children }) => {
  const transition = useMotionTransition(springSnappy);

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={transition}
      style={{ width: '100%' }}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
