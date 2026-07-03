/**
 * Normalisation centralisée des erreurs API (DRF / axios).
 */

export class ApiValidationError extends Error {
  constructor(message, fieldErrors = {}) {
    super(message);
    this.name = 'ApiValidationError';
    this.fieldErrors = fieldErrors;
  }
}

const normalizeValue = (value) => {
  if (value == null) {
    return '';
  }

  if (Array.isArray(value)) {
    return value.map(normalizeValue).filter(Boolean).join(' ');
  }

  if (typeof value === 'object') {
    return Object.values(value).map(normalizeValue).filter(Boolean).join(' ');
  }

  return String(value);
};

export const parseApiError = (error, fallback = 'Une erreur est survenue.') => {
  const data = error?.response?.data;

  if (!data) {
    return {
      message: error?.message || fallback,
      fieldErrors: {},
    };
  }

  if (typeof data === 'string') {
    return { message: data, fieldErrors: {} };
  }

  if (data.detail) {
    return {
      message: normalizeValue(data.detail),
      fieldErrors: {},
    };
  }

  const fieldErrors = {};
  let genericMessage = '';

  Object.entries(data).forEach(([key, value]) => {
    const text = normalizeValue(value);

    if (!text) {
      return;
    }

    if (key === 'non_field_errors') {
      genericMessage = text;
      return;
    }

    fieldErrors[key] = text;
  });

  const firstFieldMessage = Object.values(fieldErrors)[0];

  return {
    message: genericMessage || firstFieldMessage || fallback,
    fieldErrors,
  };
};

export const throwApiValidationError = (error, fallback) => {
  const parsed = parseApiError(error, fallback);
  throw new ApiValidationError(parsed.message, parsed.fieldErrors);
};

export const applyApiFieldErrors = (fieldErrors, setFieldErrors) => {
  if (!fieldErrors || !Object.keys(fieldErrors).length) {
    return;
  }

  setFieldErrors((previous) => ({ ...previous, ...fieldErrors }));
};
