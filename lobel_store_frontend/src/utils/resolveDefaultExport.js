/**
 * Résout les exports CJS/ESM imbriqués (ex. react-phone-input-2 via Vite).
 */
export const resolveDefaultExport = (moduleExport) => {
  if (!moduleExport) {
    return moduleExport;
  }

  if (typeof moduleExport === 'function') {
    return moduleExport;
  }

  if (moduleExport.default) {
    return resolveDefaultExport(moduleExport.default);
  }

  return moduleExport;
};
