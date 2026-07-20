export const AUTH_ERROR_CODES = Object.freeze({
  INVALID_CREDENTIALS: 'invalid_credentials',
  ACCOUNT_UNAVAILABLE: 'account_unavailable',
  THROTTLED: 'throttled',
  NETWORK: 'network',
  SERVER: 'server',
  SESSION_EXPIRED: 'session_expired',
  SESSION_REVOKED: 'session_revoked',
  VALIDATION: 'validation',
  UNKNOWN: 'unknown',
});

export class AuthError extends Error {
  constructor(code, message, options = {}) {
    super(message, options);
    this.name = 'AuthError';
    this.code = code;
    this.fieldErrors = options.fieldErrors || {};
    this.retryAfter = options.retryAfter || null;
    this.status = options.status || null;
  }
}

const messages = {
  invalid_credentials: 'Email ou mot de passe incorrect.',
  account_unavailable: 'Ce compte ne peut pas être utilisé actuellement.',
  throttled: 'Trop de tentatives. Veuillez patienter avant de réessayer.',
  network: 'Connexion au serveur impossible. Vérifiez votre réseau.',
  server: 'Le service est momentanément indisponible.',
  session_expired: 'Votre session a expiré. Veuillez vous reconnecter.',
  session_revoked: 'Votre session n’est plus valide. Veuillez vous reconnecter.',
  validation: 'Certaines informations sont invalides.',
  unknown: 'Une erreur inattendue est survenue.',
};

const normalizeFields = (data) => {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return {};
  return Object.fromEntries(Object.entries(data)
    .filter(([key]) => key !== 'detail' && key !== 'code')
    .map(([key, value]) => [key, Array.isArray(value) ? value.join(' ') : String(value)]));
};

export const normalizeAuthError = (error, fallbackCode = AUTH_ERROR_CODES.UNKNOWN) => {
  if (error instanceof AuthError) return error;
  if (!error?.response) return new AuthError(AUTH_ERROR_CODES.NETWORK, messages.network, { cause: error });
  const { status, data, headers } = error.response;
  let code = fallbackCode;
  if (status === 429) code = AUTH_ERROR_CODES.THROTTLED;
  else if (status >= 500) code = AUTH_ERROR_CODES.SERVER;
  else if (status === 401 && data?.code === 'token_not_valid') code = AUTH_ERROR_CODES.SESSION_EXPIRED;
  else if (status === 401 && /indisponible|inactive|invalides/i.test(data?.detail || '')) {
    code = AUTH_ERROR_CODES.INVALID_CREDENTIALS;
  } else if (status === 401) code = AUTH_ERROR_CODES.SESSION_REVOKED;
  else if (status === 400) code = AUTH_ERROR_CODES.VALIDATION;
  return new AuthError(code, messages[code], {
    cause: error,
    status,
    fieldErrors: normalizeFields(data),
    retryAfter: headers?.['retry-after'] || null,
  });
};
