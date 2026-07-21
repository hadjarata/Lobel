import React from 'react';
import './Primitives.css';

const Container = ({
  as: component = 'div',
  size = 'default',
  children,
  className = '',
  ...props
}) => React.createElement(
  component,
  {
    className: `ds-container ${size !== 'default' ? `ds-container--${size}` : ''} ${className}`.trim(),
    ...props,
  },
  children,
);

export default Container;
