import { beforeEach, describe, expect, it } from 'vitest';
import { AUTH_STORAGE_KEY } from './authConstants';
import {
  clearStoredSession,
  hasRestorableSession,
  readStoredSession,
  saveStoredSession,
} from './authStorage';

describe('authStorage', () => {
  beforeEach(() => localStorage.clear());
  it('enregistre uniquement le refresh token', () => {
    saveStoredSession({ access: 'ignored', refresh: 'refresh-1' });
    expect(JSON.parse(localStorage.getItem(AUTH_STORAGE_KEY))).toEqual({ refresh: 'refresh-1' });
  });
  it('restaure une session valide', () => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ refresh: 'refresh-1' }));
    expect(readStoredSession()).toEqual({ refresh: 'refresh-1' });
  });
  it('supprime un JSON invalide', () => {
    localStorage.setItem(AUTH_STORAGE_KEY, '{');
    expect(readStoredSession()).toBeNull();
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });
  it('supprime une structure invalide', () => {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ access: 'access' }));
    expect(readStoredSession()).toBeNull();
  });
  it('indique si une session est restaurable', () => {
    expect(hasRestorableSession()).toBe(false);
    saveStoredSession({ refresh: 'refresh-1' });
    expect(hasRestorableSession()).toBe(true);
  });
  it('refuse un refresh vide', () => {
    expect(() => saveStoredSession({ refresh: '' })).toThrow(TypeError);
  });
  it('efface la session', () => {
    saveStoredSession({ refresh: 'refresh-1' });
    clearStoredSession();
    expect(readStoredSession()).toBeNull();
  });
});
