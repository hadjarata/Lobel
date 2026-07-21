import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

vi.stubEnv('VITE_API_BASE_URL', 'http://api.test.invalid');

vi.stubGlobal('IntersectionObserver', class IntersectionObserver {
  constructor(callback) {
    this.callback = callback;
  }

  observe(element) {
    this.callback([{
      target: element,
      isIntersecting: true,
      intersectionRatio: 1,
    }]);
  }

  unobserve() {}

  disconnect() {}
});
