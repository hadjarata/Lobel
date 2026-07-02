import React, { useEffect, useState } from 'react';
import { toast } from './toast';
import './toast.css';

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

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
        {toasts.map((item) => (
          <div
            key={item.id}
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
          </div>
        ))}
      </div>
    </>
  );
};

export default ToastProvider;
