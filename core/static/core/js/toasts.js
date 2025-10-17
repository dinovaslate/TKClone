let container;

const ensureContainer = () => {
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }
};

export const showToast = ({
  message,
  variant = 'info',
  duration = 4000,
  action,
}) => {
  ensureContainer();
  const toast = document.createElement('div');
  toast.className = `toast glass toast-${variant}`;
  toast.innerHTML = `
    <span>${message}</span>
    ${action ? `<button class="btn-ghost" type="button">${action.label}</button>` : ''}
  `;
  container.appendChild(toast);

  if (action) {
    const actionButton = toast.querySelector('button');
    actionButton.addEventListener('click', () => {
      action.handler();
      container.removeChild(toast);
    });
  }

  if (duration !== null) {
    setTimeout(() => {
      if (toast.isConnected) {
        container.removeChild(toast);
      }
    }, duration);
  }
};
