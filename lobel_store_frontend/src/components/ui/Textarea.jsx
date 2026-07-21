import React from 'react';
import { Field } from './Field';

const Textarea = ({ label, hint, error, className = '', ...props }) => (
  <Field
    as="textarea"
    label={label}
    hint={hint}
    error={error}
    className={`ds-textarea ${className}`.trim()}
    {...props}
  />
);

export default Textarea;
