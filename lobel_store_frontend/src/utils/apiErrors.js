import { ApiContractError } from '../api/contracts/contract';

export class ApiError extends Error {
  constructor(message, details = {}) {
    super(message, { cause: details.originalError });
    this.name = 'ApiError';
    Object.assign(this, {
      status: null,
      code: 'unknown',
      fieldErrors: {},
      nonFieldErrors: [],
      retryAfter: null,
      isCanceled: false,
      ...details,
    });
  }
}

export class ApiValidationError extends ApiError {
  constructor(message, fieldErrors = {}) {
    super(message, { code: 'validation_error', status: 400, fieldErrors });
    this.name = 'ApiValidationError';
  }
}

const textList = (value) => {
  if (value == null) return [];
  if (Array.isArray(value)) return value.flatMap(textList);
  if (typeof value === 'object') return Object.values(value).flatMap(textList);
  return [String(value)];
};

const statusMessage = (status, fallback) => ({
  400: 'Certaines informations sont invalides.',
  401: 'Authentification requise.',
  403: 'Vous n’avez pas accès à cette action.',
  404: 'La ressource demandée est introuvable.',
  409: 'Cette action entre en conflit avec l’état actuel.',
  429: 'Trop de requêtes. Veuillez patienter.',
  500: 'Le service est momentanément indisponible.',
  502: 'Un service externe est momentanément indisponible.',
  503: 'Le service est momentanément indisponible.',
}[status] || fallback);

export const normalizeApiError = (error, fallback = 'Une erreur est survenue.') => {
  if (error instanceof ApiError) return error;
  if (error instanceof ApiContractError) {
    return new ApiError(error.message, {
      code: 'contract_error',
      originalError: error,
    });
  }
  if (error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError' || error?.name === 'AbortError') {
    return new ApiError('Requête annulée.', { code: 'canceled', isCanceled: true, originalError: error });
  }
  if (!error?.response) {
    const timeout = error?.code === 'ECONNABORTED';
    return new ApiError(
      timeout ? 'Le serveur met trop de temps à répondre.' : 'Connexion au serveur impossible.',
      { code: timeout ? 'timeout' : 'network_error', originalError: error },
    );
  }
  const { status, data, headers } = error.response;
  const fieldErrors = {};
  const nonFieldErrors = textList(data?.non_field_errors);
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    Object.entries(data).forEach(([field, value]) => {
      if (!['detail', 'code', 'non_field_errors'].includes(field)) {
        const messages = textList(value);
        if (messages.length) fieldErrors[field] = messages.join(' ');
      }
    });
  }
  const detail = typeof data === 'string' ? data : textList(data?.detail)[0];
  return new ApiError(statusMessage(status, detail || fallback), {
    status,
    code: data?.code || (status === 400 ? 'validation_error' : `http_${status}`),
    fieldErrors,
    nonFieldErrors,
    retryAfter: headers?.['retry-after'] || null,
    originalError: error,
  });
};

export const parseApiError = (error, fallback) => {
  const normalized = normalizeApiError(error, fallback);
  return { message: normalized.message, fieldErrors: normalized.fieldErrors };
};
export const throwApiValidationError = (error, fallback) => {
  const normalized = normalizeApiError(error, fallback);
  throw new ApiValidationError(normalized.message, normalized.fieldErrors);
};
export const applyApiFieldErrors = (fieldErrors, setFieldErrors) => {
  if (fieldErrors && Object.keys(fieldErrors).length) {
    setFieldErrors((previous) => ({ ...previous, ...fieldErrors }));
  }
};
