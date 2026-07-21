import React from 'react';
import './Primitives.css';

const Badge = ({ children, variant = 'neutral', className = '', ...props }) => (
  <span
    className={`ds-badge ds-badge--${variant} ${className}`.trim()}
    {...props}
  >
    {children}
  </span>
);

export default Badge;
