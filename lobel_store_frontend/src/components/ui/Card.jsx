import React from 'react';
import './Primitives.css';

const Card = ({
  as: component = 'div',
  children,
  padded = true,
  elevated = false,
  className = '',
  ...props
}) => React.createElement(
  component,
  {
    className: [
      'ds-card',
      padded && 'ds-card--padded',
      elevated && 'ds-card--elevated',
      className,
    ].filter(Boolean).join(' '),
    ...props,
  },
  children,
);

export default Card;
