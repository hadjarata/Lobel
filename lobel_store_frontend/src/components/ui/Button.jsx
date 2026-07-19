import React from 'react';
import { motion } from 'framer-motion';
import { springTap } from '../../utils/motion';
import { useMotionTransition } from '../../utils/useMotionTransition';
import './Button.css';

const MotionButton = motion.button;

const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  onClick,
  type = 'button',
  disabled = false,
  className = '',
  ...props
}) => {
  const buttonClasses = `
    btn 
    btn-${variant} 
    btn-${size} 
    ${disabled ? 'btn-disabled' : ''} 
    ${className}
  `.trim();

  const tapTransition = useMotionTransition(springTap);

  return (
    <MotionButton
      type={type}
      className={buttonClasses}
      onClick={onClick}
      disabled={disabled}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      transition={tapTransition}
      {...props}
    >
      {children}
    </MotionButton>
  );
};

export default Button;
