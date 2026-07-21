import React, { useId } from 'react';
import './Primitives.css';

export function Field({
  as: control,
  label,
  hint,
  error,
  id,
  className = '',
  ...props
}) {
  const generatedId = useId();
  const controlId = id || generatedId;
  const hintId = hint ? `${controlId}-hint` : undefined;
  const errorId = error ? `${controlId}-error` : undefined;
  const describedBy = [props['aria-describedby'], hintId, errorId]
    .filter(Boolean)
    .join(' ') || undefined;

  const fieldControl = React.createElement(control, {
    ...props,
    className,
    id: controlId,
    'aria-describedby': describedBy,
    'aria-invalid': error ? true : props['aria-invalid'],
  });

  return (
    <div className="ds-field">
      {label && <label className="ds-field-label" htmlFor={controlId}>{label}</label>}
      {fieldControl}
      {hint && <p className="ds-field-hint" id={hintId}>{hint}</p>}
      {error && <p className="ds-field-error" id={errorId} role="alert">{error}</p>}
    </div>
  );
}
