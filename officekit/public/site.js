'use strict';
document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  const command = document.getElementById(button.dataset.copy).textContent;
  const status = document.getElementById('copy-status');
  try {
    await navigator.clipboard.writeText(command);
    button.textContent = 'Copied ✓';
    status.textContent = 'Clone command copied.';
  } catch (_) {
    status.textContent = 'Copy is unavailable. Select and copy the command shown.';
    button.textContent = 'Select command below';
  }
}));
