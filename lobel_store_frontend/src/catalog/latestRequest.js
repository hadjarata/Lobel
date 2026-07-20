export const createLatestRequest = () => {
  let sequence = 0;
  let controller = null;

  return {
    async run(task) {
      controller?.abort();
      controller = new AbortController();
      const request = ++sequence;
      try {
        const value = await task(controller.signal);
        return request === sequence ? { current: true, value } : { current: false };
      } catch (error) {
        if (request !== sequence || error?.code === 'ERR_CANCELED' || error?.name === 'AbortError') {
          return { current: false, canceled: true };
        }
        throw error;
      }
    },
    cancel() {
      sequence += 1;
      controller?.abort();
    },
  };
};

