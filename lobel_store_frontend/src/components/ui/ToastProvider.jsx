import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { toast } from './toast';
import { springSnappy, toastVariants } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './toast.css';

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const toastTransition = useMotionTransition(springSnappy);

  useEffect(() => {
    return toast.subscribe(({ action, id, message, type }) => {
      if (action === 'add') {
        setToasts((current) => [...current, { id, message, type }]);
        return;
      }

      if (action === 'remove') {
        setToasts((current) => current.filter((item) => item.id !== id));
      }
    });
  }, []);

  return (
    <>
      {children}
      <div className="toast-container" aria-live="polite" aria-atomic="true">
        <AnimatePresence mode="popLayout">
          {toasts.map((item) => (
            <motion.div
              key={item.id}
              layout
              variants={toastVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={toastTransition}
              className={`toast toast--${item.type}`}
              role="status"
            >
              <span className="toast-icon" aria-hidden="true">
                {item.type === 'success' && '✓'}
                {item.type === 'error' && '✕'}
                {item.type === 'warning' && '!'}
                {item.type === 'info' && 'i'}
              </span>
              <p className="toast-message">{item.message}</p>
              <button
                type="button"
                className="toast-close"
                aria-label="Fermer la notification"
                onClick={() => toast.dismiss(item.id)}
              >
                ×
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
};

export default ToastProvider;
