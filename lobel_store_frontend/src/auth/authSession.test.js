import { beforeEach, describe, expect, it, vi } from 'vitest';

const { requestRefresh } = vi.hoisted(() => ({ requestRefresh: vi.fn() }));
vi.mock('./authApi', () => ({ requestRefresh }));

import {
  __resetAuthSessionForTests,
  clearSession,
  establishSession,
  getAccessToken,
  getRefreshToken,
  refreshSession,
} from './authSession';

const token = (exp) => {
  const body = btoa(JSON.stringify({ exp })).replace(/=/g, '');
  return `header.${body}.signature`;
};
const validAccess = () => token(Math.floor(Date.now() / 1000) + 3600);

describe('authSession refresh', () => {
  beforeEach(() => {
    localStorage.clear();
    __resetAuthSessionForTests();
  });

  it('établit atomiquement une session', () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    expect(getAccessToken()).toBeTruthy();
    expect(getRefreshToken()).toBe('refresh-1');
  });
  it('enregistre le refresh tourné', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    requestRefresh.mockResolvedValue({ access: validAccess(), refresh: 'refresh-2' });
    await refreshSession();
    expect(getRefreshToken()).toBe('refresh-2');
  });
  it('conserve le refresh si le backend ne le tourne pas', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    requestRefresh.mockResolvedValue({ access: validAccess() });
    await refreshSession();
    expect(getRefreshToken()).toBe('refresh-1');
  });
  it('déduplique dix refresh simultanés', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    let resolve;
    requestRefresh.mockReturnValue(new Promise((done) => { resolve = done; }));
    const pending = Array.from({ length: 10 }, () => refreshSession());
    expect(requestRefresh).toHaveBeenCalledTimes(1);
    resolve({ access: validAccess(), refresh: 'refresh-2' });
    const results = await Promise.all(pending);
    expect(new Set(results).size).toBe(1);
  });
  it('rejette toute la file après un 401', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    requestRefresh.mockRejectedValue({ response: { status: 401, data: { code: 'token_not_valid' } } });
    const results = await Promise.allSettled([refreshSession(), refreshSession(), refreshSession()]);
    expect(results.every(({ status }) => status === 'rejected')).toBe(true);
    expect(getRefreshToken()).toBeNull();
  });
  it('conserve la session persistée sur panne réseau', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    requestRefresh.mockRejectedValue(new Error('offline'));
    await expect(refreshSession()).rejects.toMatchObject({ code: 'network' });
    expect(getRefreshToken()).toBe('refresh-1');
  });
  it('un logout pendant refresh empêche la restauration tardive', async () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    let resolve;
    requestRefresh.mockReturnValue(new Promise((done) => { resolve = done; }));
    const pending = refreshSession();
    clearSession('logout');
    resolve({ access: validAccess(), refresh: 'refresh-2' });
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
  it('refuse un refresh sans session', async () => {
    await expect(refreshSession()).rejects.toMatchObject({ status: 401 });
    expect(requestRefresh).not.toHaveBeenCalled();
  });
  it('nettoie access et refresh', () => {
    establishSession({ access: validAccess(), refresh: 'refresh-1' });
    clearSession();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});
