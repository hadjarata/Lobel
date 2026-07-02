const listeners = new Set();
let toastCounter = 0;

const notify = (payload) => {
  listeners.forEach((listener) => listener(payload));
};

export const toast = {
  subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  show(message, type = 'info', duration = 4000) {
    const id = ++toastCounter;

    notify({ action: 'add', id, message, type });

    if (duration > 0) {
      setTimeout(() => {
        notify({ action: 'remove', id });
      }, duration);
    }

    return id;
  },

  success(message, duration) {
    return this.show(message, 'success', duration ?? 4000);
  },

  error(message, duration) {
    return this.show(message, 'error', duration ?? 5000);
  },

  warning(message, duration) {
    return this.show(message, 'warning', duration ?? 4500);
  },

  info(message, duration) {
    return this.show(message, 'info', duration ?? 4000);
  },

  dismiss(id) {
    notify({ action: 'remove', id });
  },
};
