import React from 'react';
import { Field } from './Field';

const Input = ({ label, hint, error, className = '', ...props }) => (
  <Field
    as="input"
    label={label}
    hint={hint}
    error={error}
    className={`ds-input ${className}`.trim()}
    {...props}
  />
);

export default Input;
