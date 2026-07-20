export const getSafeInternalRedirect = (candidate, fallback = '/') => {
  const path = typeof candidate === 'string' ? candidate : candidate?.pathname;
  const search = typeof candidate === 'object' ? candidate?.search || '' : '';
  if (!path || !path.startsWith('/') || path.startsWith('//') || path.includes('\\')) return fallback;
  return `${path}${search}`;
};
