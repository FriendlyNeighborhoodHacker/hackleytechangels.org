/* ---------- Nixie title: one tube per letter, with two unlit cathodes stacked behind it ---------- */
const title = document.querySelector<HTMLElement>('.nixie')!, spill = title.querySelector<HTMLElement>('.spill')!;
{
  const pool = 'ABCDEFGHKLMNOPRSUVWXYZ';
  let n = 0;
  title.querySelectorAll<HTMLElement>('.row').forEach(row => {
    row.innerHTML = [...(row.textContent ?? '')].map(ch => {
      const g = [...pool.replace(ch, '')].sort(() => Math.random() - .5);
      return `<span class="t" aria-hidden="true" data-g1="${g[0]}" data-g2="${g[1]}" data-ch="${ch}" style="--d:${(.35 + n++ * .09).toFixed(2)}s"><span class="c">${ch}</span><i></i></span>`;
    }).join('');
  });
}

/* ---------- Nixie life ----------
   Flicker: every few seconds a tube stutters (now and then the whole display), and the light it throws dims with it.
   Cathode cycling: like a nixie clock's anti-poisoning routine, tubes flick through random letters and slow down
   onto their own one: once on load, and on any letter you hover.
   Depth: the unlit cathodes behind each letter shift with the mouse. */
if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const tubes = [...title.querySelectorAll<HTMLElement>('.t')];
  const POOL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const home = () => document.body.dataset.route === 'home' && !document.hidden;

  const flick = (t: HTMLElement, len: number) => {
    t.style.setProperty('--fk', len + 's');
    t.classList.remove('flick'); void t.offsetWidth; t.classList.add('flick');
    spill.classList.add('dim'); setTimeout(() => spill.classList.remove('dim'), len * 400);
    setTimeout(() => t.classList.remove('flick'), len * 1000 + 50);
  };
  const cycling = new WeakSet<HTMLElement>();
  const cycle = (t: HTMLElement, dur: number) => {
    if (cycling.has(t)) return; cycling.add(t);
    const c = t.querySelector<HTMLElement>('.c')!, final = t.dataset.ch ?? '';
    t.style.width = t.offsetWidth + 'px';                 // hold the slot steady while the letters change
    const start = performance.now(); let last = 0;
    (function step(now: number) {
      const k = (now - start) / dur;
      if (k >= 1) { c.textContent = final; t.style.width = ''; cycling.delete(t); return; }
      if (now - last > 40 + k * k * 160) { c.textContent = POOL[Math.random() * 26 | 0]; last = now; }   // slows like a reel
      requestAnimationFrame(step);
    })(start);
  };

  // once each tube has warmed up, retire the warm-up animation so a flicker can't restart it
  tubes.forEach(t => t.addEventListener('animationend', e => { if (e.animationName === 'warm') t.classList.add('lit'); }));
  setTimeout(() => tubes.forEach(t => t.classList.add('lit')), 2600);
  // on load: cycle in, left to right, as the tubes warm up
  tubes.forEach((t, i) => setTimeout(() => cycle(t, 700 + i * 40), 350 + i * 90));
  tubes.forEach(t => t.addEventListener('pointerenter', () => cycle(t, 520)));

  (function nextFlicker() {
    setTimeout(() => {
      if (home()) {
        const lit = tubes.filter(t => t.classList.contains('lit'));
        if (lit.length === tubes.length && Math.random() < .14) lit.forEach((t, i) => setTimeout(() => flick(t, .32), i * 18));
        else if (lit.length) flick(lit[Math.random() * lit.length | 0], .3 + Math.random() * .4);
      }
      nextFlicker();
    }, 1800 + Math.random() * 4200);
  })();

  if (matchMedia('(hover: hover)').matches) addEventListener('pointermove', e => {
    title.style.setProperty('--px', String(((e.clientX / innerWidth) - .5) * 2));
    title.style.setProperty('--py', String(((e.clientY / innerHeight) - .5) * 2));
  }, { passive: true });
}

export {};
