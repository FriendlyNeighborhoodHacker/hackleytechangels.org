/* Liquid glass: per-element displacement map built from the element's own rounded-rect shape.
   Pixels inside the bezel sample the backdrop outward along the edge normal, so the sky bends at the rim.
   Applies to every element with class "glass". Chromium only; Safari/Firefox keep the clear-blur fallback. */
const NS = 'http://www.w3.org/2000/svg';

function map(w: number, h: number, r: number, bezel: number) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const ctx = c.getContext('2d')!, img = ctx.createImageData(w, h), d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const px = x + .5 - w / 2, py = y + .5 - h / 2;
    const qx = Math.abs(px) - (w / 2 - r), qy = Math.abs(py) - (h / 2 - r);
    const ox = Math.max(qx, 0), oy = Math.max(qy, 0);
    const dist = r - (Math.hypot(ox, oy) + Math.min(Math.max(qx, qy), 0));   // distance in from the edge
    let nx = 0, ny = 0, k = 0;
    if (dist < bezel && dist > -1) {
      const t = 1 - Math.max(dist, 0) / bezel;
      k = t * t * (3 - 2 * t);                                               // smooth lens falloff
      if (qx > 0 && qy > 0) { const l = Math.hypot(qx, qy) || 1; nx = qx / l; ny = qy / l; }
      else if (qx > qy) nx = 1; else ny = 1;
      nx *= Math.sign(px) || 1; ny *= Math.sign(py) || 1;
    }
    const i = (y * w + x) * 4;
    d[i] = 128 + nx * k * 127; d[i + 1] = 128 + ny * k * 127; d[i + 2] = 128; d[i + 3] = 255;
  }
  ctx.putImageData(img, 0, 0); return c.toDataURL();
}

if ('chrome' in window && CSS.supports('backdrop-filter', 'url(#x)')) {
  const defs = document.createElementNS(NS, 'svg');
  defs.setAttribute('width', '0'); defs.setAttribute('height', '0'); defs.setAttribute('aria-hidden', 'true');
  defs.style.position = 'absolute';
  document.body.appendChild(defs);

  const els = [...document.querySelectorAll<HTMLElement>('.glass')];
  const build = (el: HTMLElement, i: number) => {
    const w = Math.round(el.offsetWidth), h = Math.round(el.offsetHeight);
    if (!w || !h) return;
    const r = Math.min(parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0, w / 2, h / 2);
    const bezel = Math.max(10, Math.min(30, Math.min(w, h) * .42));
    let f = defs.querySelector('#lg-' + i);
    if (!f) { f = document.createElementNS(NS, 'filter'); f.id = 'lg-' + i; defs.appendChild(f); }
    f.setAttribute('x', '0'); f.setAttribute('y', '0'); f.setAttribute('width', String(w)); f.setAttribute('height', String(h));
    f.setAttribute('filterUnits', 'userSpaceOnUse'); f.setAttribute('color-interpolation-filters', 'sRGB');
    f.innerHTML = `<feImage href="${map(w, h, r, bezel)}" x="0" y="0" width="${w}" height="${h}" preserveAspectRatio="none" result="m"/>
      <feDisplacementMap in="SourceGraphic" in2="m" scale="${Math.round(bezel * 2.4)}" xChannelSelector="R" yChannelSelector="G"/>`;
    el.style.setProperty('--lg', `url(#lg-${i}) blur(.6px) saturate(112%) brightness(1.04)`);
    el.classList.add('lg-on');
  };
  const timers = new WeakMap<Element, number>();
  const ro = new ResizeObserver(entries => entries.forEach(e => {
    const el = e.target as HTMLElement, i = els.indexOf(el);
    clearTimeout(timers.get(el)); timers.set(el, window.setTimeout(() => build(el, i), 80));
  }));
  els.forEach((el, i) => { build(el, i); ro.observe(el); });
}

export {};
