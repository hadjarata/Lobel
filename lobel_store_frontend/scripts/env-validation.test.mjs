import assert from 'node:assert/strict';
import test from 'node:test';

import {
  FrontendConfigurationError,
  createPublicConfig,
} from '../src/config/envValidation.js';

const environment = (overrides = {}) => ({
  VITE_APP_ENV: 'production',
  VITE_API_BASE_URL: 'https://api.example.invalid',
  VITE_ENABLE_PAYMENT_MOCK: 'false',
  VITE_ENABLE_DEBUG_LOGS: 'false',
  ...overrides,
});

const rejectsConfiguration = (rawEnvironment, mode) => {
  assert.throws(
    () => createPublicConfig(rawEnvironment, mode),
    FrontendConfigurationError,
  );
};

test('production refuse une URL absente', () => {
  rejectsConfiguration(environment({ VITE_API_BASE_URL: '' }), 'production');
});

test('production refuse HTTP', () => {
  rejectsConfiguration(
    environment({ VITE_API_BASE_URL: 'http://api.example.invalid' }),
    'production',
  );
});

test('production refuse localhost même en HTTPS', () => {
  rejectsConfiguration(
    environment({ VITE_API_BASE_URL: 'https://localhost:8000' }),
    'production',
  );
});

test('production accepte une URL HTTPS publique', () => {
  const config = createPublicConfig(environment(), 'production');
  assert.equal(config.apiBaseUrl, 'https://api.example.invalid');
});

test('staging refuse HTTP', () => {
  rejectsConfiguration(
    environment({
      VITE_APP_ENV: 'staging',
      VITE_API_BASE_URL: 'http://staging-api.example.invalid',
    }),
    'staging',
  );
});

test('staging accepte une URL HTTPS publique', () => {
  const config = createPublicConfig(
    environment({
      VITE_APP_ENV: 'staging',
      VITE_API_BASE_URL: 'https://staging-api.example.invalid',
    }),
    'staging',
  );
  assert.equal(config.mode, 'staging');
});

test('development accepte localhost en HTTP', () => {
  const config = createPublicConfig(
    environment({
      VITE_APP_ENV: 'development',
      VITE_API_BASE_URL: 'http://127.0.0.1:8000',
      VITE_ENABLE_PAYMENT_MOCK: 'true',
      VITE_ENABLE_DEBUG_LOGS: 'true',
    }),
    'development',
  );
  assert.equal(config.apiBaseUrl, 'http://127.0.0.1:8000');
});

test('production refuse le paiement mock', () => {
  rejectsConfiguration(
    environment({ VITE_ENABLE_PAYMENT_MOCK: 'true' }),
    'production',
  );
});

test('une URL contenant des identifiants est refusée', () => {
  rejectsConfiguration(
    environment({
      VITE_API_BASE_URL: 'https://user:password@api.example.invalid',
    }),
    'production',
  );
});

test('le slash final est normalisé', () => {
  const config = createPublicConfig(
    environment({ VITE_API_BASE_URL: 'https://api.example.invalid///' }),
    'production',
  );
  assert.equal(config.apiBaseUrl, 'https://api.example.invalid');
});
