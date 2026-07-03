/**
 * Diagnostic Register – exécuter : node scripts/diagnose-register.mjs
 * depuis lobel_store_frontend (avec deps installées)
 */
import React from 'react';
import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';

const tests = [];

async function run(name, fn) {
  try {
    await fn();
    tests.push({ name, ok: true });
    console.log(`✓ ${name}`);
  } catch (error) {
    tests.push({ name, ok: false, error });
    console.error(`✗ ${name}`);
    console.error('  ', error?.stack || error?.message || error);
  }
}

await run('import country-telephone-data', async () => {
  const countryData = (await import('country-telephone-data')).default;
  if (!countryData?.allCountries?.length) {
    throw new Error('allCountries missing or empty');
  }
  console.log('    sample row:', countryData.allCountries[0]);
});

await run('import react-phone-input-2', async () => {
  const mod = await import('react-phone-input-2');
  const PhoneInput = mod.default ?? mod;
  if (typeof PhoneInput !== 'function') {
    throw new Error(`PhoneInput type=${typeof PhoneInput}`);
  }
});

await run('import react-select', async () => {
  const mod = await import('react-select');
  const Select = mod.default ?? mod;
  if (typeof Select !== 'function') {
    throw new Error(`Select type=${typeof Select}`);
  }
});

await run('render PhoneInput alone (SSR)', async () => {
  const PhoneInput = (await import('react-phone-input-2')).default;
  renderToString(React.createElement(PhoneInput, { country: 'fr', value: '' }));
});

await run('render Select alone (SSR)', async () => {
  const Select = (await import('react-select')).default;
  renderToString(
    React.createElement(Select, {
      options: [{ label: 'France', value: 'FR' }],
      value: { label: 'France', value: 'FR' },
    }),
  );
});

await run('render Register page (SSR + MemoryRouter)', async () => {
  const Register = (await import('../src/pages/auth/Register.jsx')).default;

  const AuthContext = React.createContext(null);
  const mockAuth = {
    register: async () => ({}),
    loading: false,
    login: async () => ({}),
    logout: () => {},
    user: null,
    isAuthenticated: false,
    requireAuth: () => false,
  };

  const Wrapper = ({ children }) =>
    React.createElement(
      MemoryRouter,
      { initialEntries: ['/register'] },
      React.createElement(AuthContext.Provider, { value: mockAuth }, children),
    );

  // Register uses useAuth from real context – patch via dynamic import mock won't work easily.
  // Render minimal tree with only problematic child components instead.
  void Register;
  void Wrapper;
  throw new Error('Skipped full Register SSR – useAuth requires AuthProvider; see component tests below');
});

await run('buildCountryOptions utility', async () => {
  const countryData = (await import('country-telephone-data')).default;
  const { buildCountryOptions } = await import('../src/utils/countryTelephone.js');
  const options = buildCountryOptions(countryData);
  if (!options.length) throw new Error('no options');
  console.log('    first option:', options[0]);
});

console.log('\n--- Summary ---');
const failed = tests.filter((t) => !t.ok);
if (failed.length) {
  console.log(`${failed.length} test(s) failed`);
  process.exit(1);
}
console.log('All import/SSR checks passed');
