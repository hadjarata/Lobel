import React from 'react';
import { Field } from './Field';

const Select = ({ label, hint, error, className = '', children, ...props }) => (
  <Field
    as="select"
    label={label}
    hint={hint}
    error={error}
    className={`ds-select ${className}`.trim()}
    {...props}
  >
    {children}
  </Field>
);

export default Select;
