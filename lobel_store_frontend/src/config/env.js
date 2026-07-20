import { createPublicConfig } from './envValidation';

export const publicConfig = createPublicConfig(import.meta.env, import.meta.env.MODE);
