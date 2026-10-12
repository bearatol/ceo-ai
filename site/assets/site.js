'use strict';
(() => {
  const panel = document.querySelector('.installer');
  const hosts = document.getElementById('host-choice');
  const prompt = document.getElementById('install-prompt');
  const copy = document.getElementById('copy');
  const status = document.getElementById('copy-status');
  const activation = document.getElementById('activation');
  const commands = new Map([
    ['Codex', ['ceo-ai:ceo-ai', '$ceo-ai']],
    ['Claude Code', ['/ceo-ai:ceo-ai', '/ceo-ai']],
    ['Cursor', [null, '/ceo-ai']]
  ]);
  const instructions = 'https://github.com/bearatol/ceo-ai/blob/v0.4.0/INSTALL.md';
  if (!panel || !hosts || !prompt || !copy || !status || !activation) return;
  const update = () => {
    const selected = hosts.querySelector('input:checked');
    if (!selected || !commands.has(selected.value)) return;
    prompt.value = panel.dataset.template.replace('{host}', selected.value) + '\n' + instructions;
    const [plugin, project] = commands.get(selected.value);
    const parts = [panel.dataset.after + ' '];
    if (plugin) {
      const command = document.createElement('code');
      command.textContent = plugin;
      parts.push(panel.dataset.plugin + ' ', command, '; ');
    }
    const command = document.createElement('code');
    command.textContent = project;
    parts.push(panel.dataset.project + ' ', command, panel.dataset.afterEnd);
    activation.replaceChildren(...parts);
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

(() => {
  const visual = document.querySelector('.command-visual');
  const button = visual?.querySelector('.motion-toggle');
  const stage = visual?.querySelector('.flow-stage');
  if (!visual || !button || !stage) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = false, visible = true, phase = 0, timer;
  const sync = () => {
    clearInterval(timer);
    const active = !paused && !reduced.matches && visible && !document.hidden;
    visual.classList.toggle('motion-active', active);
    button.hidden = reduced.matches;
    button.textContent = paused ? visual.dataset.play : visual.dataset.pause;
    if (active) timer = setInterval(() => {
      phase = (phase + 1) % 3;
      visual.dataset.phase = String(phase);
      stage.textContent = visual.getAttribute('data-stage-' + phase);
    }, 3600);
  };
  button.addEventListener('click', () => { paused = !paused; sync(); });
  reduced.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    sync();
  }).observe(visual);
  sync();
})();
