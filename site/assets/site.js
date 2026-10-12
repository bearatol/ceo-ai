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
  const instructions = 'https://github.com/bearatol/ceo-ai/blob/main/INSTALL.md';
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
  let paused = false, visible = false, phase = 0;
  const sync = () => {
    const active = !paused && !reduced.matches && visible && !document.hidden;
    visual.classList.toggle('motion-active', active);
    button.hidden = reduced.matches;
    const label = paused ? visual.dataset.play : visual.dataset.pause;
    button.setAttribute('aria-label', label);
    button.title = label;
    button.dataset.paused = String(paused);
  };
  visual.addEventListener('animationiteration', event => {
    if (event.animationName !== 'task-flow' || !event.target.classList.contains('route-0') ||
        !visual.classList.contains('motion-active')) return;
    phase = (phase + 1) % 3;
    visual.dataset.phase = String(phase);
    stage.textContent = visual.getAttribute('data-stage-' + phase);
  });
  button.addEventListener('click', () => { paused = !paused; sync(); });
  reduced.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    sync();
  }).observe(visual);
  else visible = true;
  sync();
})();

// Anchor offsets follow the actual sticky header, including translated labels.
(() => {
  const header = document.querySelector('.header');
  if (!header) return;
  const resize = () => document.documentElement.style.setProperty('--header-height', header.getBoundingClientRect().height + 'px');
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(header);
  else window.addEventListener('resize', resize);
  resize();
})();
