import { loadEnv } from 'vite';
import { createPublicConfig } from '../src/config/envValidation.js';

const readMode = (argumentsList) => {
  const index = argumentsList.indexOf('--mode');
  if (index === -1 || !argumentsList[index + 1]) {
    throw new Error('Usage : node scripts/validate-env.mjs --mode <mode>');
  }
  return argumentsList[index + 1];
};

const mode = readMode(process.argv.slice(2));
const fileEnvironment = loadEnv(mode, process.cwd(), 'VITE_');
const processEnvironment = Object.fromEntries(
  Object.entries(process.env).filter(([name]) => name.startsWith('VITE_')),
);
const config = createPublicConfig(
  { ...fileEnvironment, ...processEnvironment },
  mode,
);

console.log(
  `Configuration ${config.mode} valide : API=${config.apiBaseUrl}, mock=${config.paymentMockEnabled}, debug=${config.debugLogsEnabled}`,
);
