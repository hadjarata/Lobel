const SUPPORTED_MODES = new Set(['development', 'test', 'staging', 'production']);
const STRICT_MODES = new Set(['staging', 'production']);
const LOCAL_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0', '[::1]', '::1']);

export class FrontendConfigurationError extends Error {
  constructor(message) {
    super(`Configuration frontend invalide : ${message}`);
    this.name = 'FrontendConfigurationError';
  }
}

const clean = (value) => String(value ?? '').trim();

const readBoolean = (rawValue, name, defaultValue) => {
  const value = clean(rawValue).toLowerCase();
  if (!value) {
    return defaultValue;
  }
  if (value === 'true') {
    return true;
  }
  if (value === 'false') {
    return false;
  }
  throw new FrontendConfigurationError(`${name} doit valoir "true" ou "false".`);
};

const isLocalHostname = (hostname) => {
  const normalized = hostname.toLowerCase();
  return LOCAL_HOSTS.has(normalized) || normalized.endsWith('.local');
};

export const validateApiBaseUrl = (rawValue, mode) => {
  const value = clean(rawValue);
  if (!value) {
    throw new FrontendConfigurationError(
      `VITE_API_BASE_URL est obligatoire en mode ${mode}.`,
    );
  }

  let url;
  try {
    url = new URL(value);
  } catch {
    throw new FrontendConfigurationError(
      'VITE_API_BASE_URL doit être une URL absolue valide.',
    );
  }

  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new FrontendConfigurationError(
      'VITE_API_BASE_URL doit utiliser le protocole HTTP ou HTTPS.',
    );
  }
  if (url.username || url.password) {
    throw new FrontendConfigurationError(
      'VITE_API_BASE_URL ne doit contenir aucun identifiant.',
    );
  }
  if (url.hash) {
    throw new FrontendConfigurationError(
      'VITE_API_BASE_URL ne doit contenir aucun fragment.',
    );
  }
  if (url.search) {
    throw new FrontendConfigurationError(
      'VITE_API_BASE_URL ne doit contenir aucun paramètre de requête.',
    );
  }

  if (STRICT_MODES.has(mode)) {
    if (url.protocol !== 'https:') {
      throw new FrontendConfigurationError(
        `VITE_API_BASE_URL doit utiliser HTTPS en mode ${mode}.`,
      );
    }
    if (isLocalHostname(url.hostname)) {
      throw new FrontendConfigurationError(
        `VITE_API_BASE_URL ne peut pas cibler un hôte local en mode ${mode}.`,
      );
    }
  }

  return value.replace(/\/+$/, '');
};

export const createPublicConfig = (rawEnvironment, viteMode) => {
  const mode = clean(viteMode).toLowerCase();
  if (!SUPPORTED_MODES.has(mode)) {
    throw new FrontendConfigurationError(
      `mode "${mode || '(vide)'}" non pris en charge.`,
    );
  }

  const declaredMode = clean(rawEnvironment.VITE_APP_ENV).toLowerCase();
  if (declaredMode && declaredMode !== mode) {
    throw new FrontendConfigurationError(
      `VITE_APP_ENV="${declaredMode}" ne correspond pas au mode Vite "${mode}".`,
    );
  }
  if (STRICT_MODES.has(mode) && !declaredMode) {
    throw new FrontendConfigurationError(
      `VITE_APP_ENV est obligatoire en mode ${mode}.`,
    );
  }

  const paymentMockEnabled = readBoolean(
    rawEnvironment.VITE_ENABLE_PAYMENT_MOCK,
    'VITE_ENABLE_PAYMENT_MOCK',
    false,
  );
  if (STRICT_MODES.has(mode) && paymentMockEnabled) {
    throw new FrontendConfigurationError(
      `le paiement mock est interdit en mode ${mode}.`,
    );
  }

  const debugLogsEnabled = readBoolean(
    rawEnvironment.VITE_ENABLE_DEBUG_LOGS,
    'VITE_ENABLE_DEBUG_LOGS',
    mode === 'development',
  );
  if (STRICT_MODES.has(mode) && debugLogsEnabled) {
    throw new FrontendConfigurationError(
      `les logs de debug sont interdits en mode ${mode}.`,
    );
  }

  return Object.freeze({
    mode,
    appName: clean(rawEnvironment.VITE_APP_NAME) || 'LobelStore',
    apiBaseUrl: validateApiBaseUrl(rawEnvironment.VITE_API_BASE_URL, mode),
    paymentMockEnabled,
    debugLogsEnabled,
    isDevelopment: mode === 'development',
    isTest: mode === 'test',
    isStaging: mode === 'staging',
    isProduction: mode === 'production',
  });
};
