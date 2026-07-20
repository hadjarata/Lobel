import { publicConfig } from '../config/env';

const write = (method, values) => {
  if (publicConfig.debugLogsEnabled) {
    console[method](...values);
  }
};

export const logger = Object.freeze({
  debug: (...values) => write('debug', values),
  info: (...values) => write('info', values),
  warn: (...values) => write('warn', values),
  error: (...values) => write('error', values),
});
