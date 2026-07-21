import React from 'react';
import { motion } from 'framer-motion';
import { springTap } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './Primitives.css';
import './Button.css';

const MotionButton = motion.button;

const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  loading = false,
  loadingLabel = 'Chargement',
  onClick,
  type = 'button',
  disabled = false,
  className = '',
  ...props
}) => {
  const isDisabled = disabled || loading;
  const buttonClasses = `
    btn 
    btn-${variant} 
    btn-${size} 
    ${isDisabled ? 'btn-disabled' : ''}
    ${loading ? 'btn-loading' : ''}
    ${className}
  `.trim();

  const tapTransition = useMotionTransition(springTap);

  return (
    <MotionButton
      type={type}
      className={buttonClasses}
      onClick={onClick}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      whileTap={isDisabled ? undefined : { scale: 0.98 }}
      transition={tapTransition}
      {...props}
      aria-label={loading ? loadingLabel : props['aria-label']}
    >
      <span className="btn-label" aria-hidden={loading || undefined}>{children}</span>
      {loading && <span className="btn-spinner" aria-hidden="true" />}
      {loading && <span className="ds-sr-only">{loadingLabel}</span>}
    </MotionButton>
  );
};

export default Button;
