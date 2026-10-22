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
      const label = selected.value === 'Codex' ? panel.dataset.pluginSelect : panel.dataset.plugin;
      parts.push(label + ' ', command, '; ');
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
  const pointer = window.matchMedia('(hover: hover) and (pointer: fine) and (min-width: 801px)');
  const scene = visual.querySelector('.core-scene');
  let paused = false, visible = false, phase = 0;
  let frame = 0;
  const resetTilt = () => {
    window.cancelAnimationFrame(frame);
    frame = 0;
    scene?.style.removeProperty('--tilt-x');
    scene?.style.removeProperty('--tilt-y');
  };
  const sync = () => {
    const active = !paused && !reduced.matches && visible && !document.hidden;
    visual.classList.toggle('motion-active', active);
    button.hidden = reduced.matches;
    const label = paused ? visual.dataset.play : visual.dataset.pause;
    button.setAttribute('aria-label', label);
    button.title = label;
    button.dataset.paused = String(paused);
    if (!active || !pointer.matches) resetTilt();
  };
  visual.addEventListener('animationiteration', event => {
    if (event.animationName !== 'task-flow' || !event.target.classList.contains('route-0') ||
        !visual.classList.contains('motion-active')) return;
    phase = (phase + 1) % 3;
    visual.dataset.phase = String(phase);
    stage.textContent = visual.getAttribute('data-stage-' + phase);
  });
  button.addEventListener('click', () => { paused = !paused; sync(); });
  visual.addEventListener('pointermove', event => {
    if (!scene || event.pointerType !== 'mouse' || !pointer.matches ||
        !visual.classList.contains('motion-active')) return;
    window.cancelAnimationFrame(frame);
    frame = window.requestAnimationFrame(() => {
      const bounds = visual.getBoundingClientRect();
      const x = Math.max(-1, Math.min(1, (event.clientX - bounds.left) / bounds.width * 2 - 1));
      const y = Math.max(-1, Math.min(1, (event.clientY - bounds.top) / bounds.height * 2 - 1));
      scene.style.setProperty('--tilt-x', (-y * 4).toFixed(2) + 'deg');
      scene.style.setProperty('--tilt-y', (x * 4).toFixed(2) + 'deg');
      frame = 0;
    });
  });
  visual.addEventListener('pointerleave', resetTilt);
  visual.addEventListener('pointercancel', resetTilt);
  pointer.addEventListener('change', sync);
  reduced.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting && entries[0].intersectionRatio >= .12;
    sync();
  }, { threshold: .12 }).observe(visual);
  else visible = true;
  sync();
})();

// Reveal only small illustrations and cards. Content is visible before JS runs.
(() => {
  if (!('IntersectionObserver' in window)) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      if (!reduced.matches && !entry.target.contains(document.activeElement)) {
        entry.target.classList.add('reveal-in');
      }
      observer.unobserve(entry.target);
    }
  }, { threshold: .12, rootMargin: '0px 0px -32px 0px' });
  document.querySelectorAll('.method-grid article, .scan-preview, .pattern-preview, .module-options article')
    .forEach(element => observer.observe(element));
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

// The setup prompt is static text; copying does not start setup or grant access.
(() => {
  const prompt = document.getElementById('deep-scan-prompt');
  const button = document.getElementById('copy-deep-scan');
  const status = document.getElementById('deep-scan-status');
  if (!prompt || !button || !status) return;
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(prompt.value);
      status.textContent = button.dataset.copied;
    } catch {
      prompt.focus();
      prompt.select();
      status.textContent = button.dataset.fallback;
    }
  });
  button.hidden = false;
})();
