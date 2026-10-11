'use strict';
(() => {
  const panel = document.querySelector('.installer');
  const hosts = document.getElementById('host-choice');
  const prompt = document.getElementById('install-prompt');
  const copy = document.getElementById('copy');
  const status = document.getElementById('copy-status');
  const activation = document.getElementById('activation');
  const commands = new Map([['Codex', '$ceo-ai'], ['Claude Code', '/ceo-ai'], ['Cursor', '/ceo-ai']]);
  const instructions = 'https://github.com/bearatol/ceo-ai/blob/v0.2.0/INSTALL.md';
  if (!panel || !hosts || !prompt || !copy || !status || !activation) return;
  const update = () => {
    const selected = hosts.querySelector('input:checked');
    if (!selected || !commands.has(selected.value)) return;
    prompt.value = panel.dataset.template.replace('{host}', selected.value) + '\n' + instructions;
    const command = document.createElement('code');
    command.textContent = commands.get(selected.value);
    activation.replaceChildren(panel.dataset.after + ' ', command, ' ' + panel.dataset.afterEnd);
    status.textContent = '';
  };
  hosts.addEventListener('change', update);
  copy.addEventListener('click', async () => {
    const message = prompt.value;
    try {
      await navigator.clipboard.writeText(message);
      status.textContent = panel.dataset.copied;
    } catch {
      prompt.focus();
      prompt.select();
      status.textContent = panel.dataset.fallback;
    }
  });
  update();
  hosts.hidden = false;
  copy.hidden = false;
})();
