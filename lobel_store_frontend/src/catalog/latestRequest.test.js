import { describe, expect, it, vi } from 'vitest';
import { createLatestRequest } from './latestRequest';

const deferred = () => {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};

describe('latest request wins', () => {
  it('returns the first result when it is still current', async () => {
    const runner = createLatestRequest();
    await expect(runner.run(() => Promise.resolve('ok'))).resolves.toEqual({ current: true, value: 'ok' });
  });

  it('marks an older response stale', async () => {
    const runner = createLatestRequest();
    const first = deferred();
    const firstRun = runner.run(() => first.promise);
    const secondRun = runner.run(() => Promise.resolve('new'));
    first.resolve('old');
    await expect(firstRun).resolves.toEqual({ current: false });
    await expect(secondRun).resolves.toEqual({ current: true, value: 'new' });
  });

  it('aborts the preceding signal', async () => {
    const runner = createLatestRequest();
    let firstSignal;
    runner.run((signal) => { firstSignal = signal; return new Promise(() => {}); });
    await runner.run(() => Promise.resolve());
    expect(firstSignal.aborted).toBe(true);
  });

  it('cancel aborts the current signal', () => {
    const runner = createLatestRequest();
    let signal;
    runner.run((value) => { signal = value; return new Promise(() => {}); });
    runner.cancel();
    expect(signal.aborted).toBe(true);
  });

  it('suppresses canceled axios errors', async () => {
    const runner = createLatestRequest();
    await expect(runner.run(() => Promise.reject({ code: 'ERR_CANCELED' })))
      .resolves.toEqual({ current: false, canceled: true });
  });

  it('suppresses AbortError', async () => {
    const runner = createLatestRequest();
    await expect(runner.run(() => Promise.reject({ name: 'AbortError' })))
      .resolves.toEqual({ current: false, canceled: true });
  });

  it('propagates current server errors', async () => {
    const runner = createLatestRequest();
    const error = new Error('server');
    await expect(runner.run(() => Promise.reject(error))).rejects.toBe(error);
  });

  it('calls every supplied task once', async () => {
    const runner = createLatestRequest();
    const task = vi.fn(() => Promise.resolve(1));
    await runner.run(task);
    await runner.run(task);
    expect(task).toHaveBeenCalledTimes(2);
  });
});
