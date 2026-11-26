/* The single-page shell: hash routing between the full-screen views, smooth wheel scrolling,
   "keep scrolling" into the next page, the drifting sky, the nav dot and the portfolio section pills.
   Page order and titles come from src/data/menu.ts. */
import { menu } from '../data/menu';
import { siteConfig } from '../data/siteConfig';

const html = document.documentElement, body = document.body;
const ORDER = ['home', ...menu.map(m => m.route)];
const TITLES: Record<string, string> = { home: siteConfig.siteName, ...Object.fromEntries(menu.map(m => [m.route, m.title])) };
/* names used in the "Keep scrolling for …" cue */
const NAMES: Record<string, string> = { ...TITLES, home: 'Home' };
const views = Object.fromEntries(ORDER.map(k => [k, document.getElementById(k)!])) as Record<string, HTMLElement>;
const subs = [...document.querySelectorAll<HTMLElement>('.sub')];
const doves = [...document.querySelectorAll<HTMLElement>('.dove')];
const offDoves = doves.filter(d => !/d-a|d-e/.test(d.className));   // the ones that leave the frame on sub-pages
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const routeOf = (h: string) => { const k = (h || '').replace(/^#/, ''); return ORDER.includes(k) ? k : 'home'; };
const frame = () => new Promise<void>(r => requestAnimationFrame(() => requestAnimationFrame(() => r())));
let current = routeOf(location.hash);

function setChrome(r: string) {
  body.dataset.route = r;
  document.querySelectorAll<HTMLElement>('[data-route-link]').forEach(a =>
    a.dataset.routeLink === r ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
  document.title = r === 'home' ? TITLES.home : TITLES[r] + ' — ' + siteConfig.siteName;
}

let leaveT = 0;
function go(r: string) {
  if (r === current) return;
  const from = views[current], to = views[r], dir = ORDER.indexOf(r) < ORDER.indexOf(current) ? 'back' : 'fwd';
  if (r === 'home') {                          // park departed doves on the left, unseen, so they fly back in forwards
    offDoves.forEach(d => d.classList.add('no-tr'));
    body.dataset.dir = 'back'; void body.offsetWidth;
    offDoves.forEach(d => d.classList.remove('no-tr'));
  } else body.dataset.dir = 'fwd';
  html.dataset.dir = dir;
  from.classList.add('leaving');
  void to.offsetWidth;                            // commit the entering start pose for this direction
  from.classList.remove('is-active');
  to.classList.add('is-active');
  if (r !== 'home') to.scrollTop = 0;
  if (r === 'portfolio') placePill(true);
  setChrome(r);
  clearTimeout(leaveT); leaveT = window.setTimeout(() => from.classList.remove('leaving'), 650);
  current = r;
}

// first paint: drop doves in place, then let the current view's text stagger in
setChrome(current);
doves.forEach(d => d.classList.add('no-tr'));
frame().then(() => { doves.forEach(d => d.classList.remove('no-tr')); views[current].classList.add('is-active'); placePill(true); });
addEventListener('hashchange', () => go(routeOf(location.hash)));

// doves step aside while a page is scrolled, and come back at the top
subs.forEach(v => v.addEventListener('scroll', () =>
  body.classList.toggle('scrolled', v.scrollTop > 140), { passive: true }));
addEventListener('hashchange', () => body.classList.remove('scrolled'));

/* ---------- smooth scrolling + scroll-through pages ----------
   Wheel scrolling inside a page eases toward its target (exponential smoothing, frame-rate independent).
   Keep scrolling past the bottom and a pill fills up, then the next page transitions in; past the top goes back.
   Order follows the menu: Home, Portfolio, Angels, Story, Contact. Touch and keyboard do the same. */
const PULL = 260;
const hint = document.createElement('div');
hint.className = 'edge-hint'; hint.setAttribute('aria-hidden', 'true');
hint.innerHTML = '<svg class="eh-ring" viewBox="0 0 24 24"><circle class="track" cx="12" cy="12" r="11"/><circle class="fill" cx="12" cy="12" r="11" pathLength="1"/><path d="M12 7.5v8.5M8.5 12.5 12 16l3.5-3.5"/></svg><span class="eh-l"></span>';
document.body.appendChild(hint);
const hintLabel = hint.querySelector<HTMLElement>('.eh-l')!;

interface ScrollState { y: number; target: number; raf: number }
const ss = new Map<HTMLElement, ScrollState>();
const st = (v: HTMLElement) => {
  let s = ss.get(v);
  if (!s) { s = { y: v.scrollTop, target: v.scrollTop, raf: 0 }; ss.set(v, s); }
  return s;
};
const maxY = (v: HTMLElement) => Math.max(0, v.scrollHeight - v.clientHeight);
function animate(v: HTMLElement) {
  const s = st(v); if (s.raf) return;
  let last = performance.now();
  const step = (now: number) => {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    s.y += (s.target - s.y) * (1 - Math.exp(-dt * 8.5));
    if (Math.abs(s.target - s.y) < .5) s.y = s.target;
    v.scrollTop = s.y;
    s.raf = s.y !== s.target ? requestAnimationFrame(step) : 0;
  };
  s.raf = requestAnimationFrame(step);
}
function smoothTo(v: HTMLElement, y: number) {
  const s = st(v); s.target = Math.max(0, Math.min(maxY(v), y));
  if (reduce) { v.scrollTop = s.y = s.target; return; }
  animate(v);
}
function sync(v: HTMLElement) { const s = st(v); cancelAnimationFrame(s.raf); s.raf = 0; s.y = s.target = v.scrollTop; }

let pull = 0, pullDir = 0, pullT = 0, cooldown = 0;
/* after a page change: start at the top and ignore input until the gesture's momentum has died out
   (at least ~1s, extended while momentum events keep arriving, capped at 2.6s) */
let lockUntil = 0, lockStart = 0;
const locked = () => performance.now() < lockUntil;
function lockInput(ms: number) {
  lockStart = performance.now(); lockUntil = lockStart + ms;
  body.classList.add('scroll-locked');
  (function check() {
    if (locked()) { setTimeout(check, Math.max(30, lockUntil - performance.now())); return; }
    body.classList.remove('scroll-locked');
    const v = views[current]; if (v && v !== views.home) sync(v);
  })();
}

/* rubber band: while you push past an edge the page lifts (or drops) and dims a touch, following your scroll;
   stop short and it springs back. Values are smoothed so discrete wheel clicks still feel continuous. */
let pullShown = 0, pullTarget = 0, pullRaf = 0;
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
function setPull(t: number) { pullTarget = t; if (!pullRaf) pullRaf = requestAnimationFrame(pullTick); }
function pullTick() {
  pullShown += (pullTarget - pullShown) * .18;
  if (Math.abs(pullTarget - pullShown) < .002) pullShown = pullTarget;
  hint.style.setProperty('--p', pullShown.toFixed(3));
  if (!reduce) {
    const v = views[current], e = easeOut(pullShown);
    v.style.translate = e ? `0 ${(-pullDir * e * 46).toFixed(2)}px` : '';
    v.style.opacity = e ? (1 - e * .28).toFixed(3) : '';
  }
  pullRaf = pullShown !== pullTarget ? requestAnimationFrame(pullTick) : 0;
}

/* one continuous sky: it drifts with where you are in the whole site (page order + how far down the page) */
const sky = document.getElementById('sky')!;
function journey() {
  const i = ORDER.indexOf(current), v = views[current];
  const f = current === 'home' ? 0 : v.scrollTop / Math.max(1, maxY(v));
  sky.style.setProperty('--j', ((i + f * .85) / (ORDER.length - 1)).toFixed(4));
}

/* sliding nav dot */
const navDot = document.querySelector<HTMLElement>('.nav-dot')!;
function placeDot() {
  const a = document.querySelector<HTMLElement>('nav a.link[aria-current=page]');
  if (!a) { navDot.style.opacity = '0'; return; }
  navDot.style.transform = `translateX(${a.offsetLeft + a.offsetWidth / 2}px)`;
  navDot.style.opacity = '1';
}
addEventListener('resize', placeDot);
document.fonts?.ready.then(placeDot);

const neighbour = (dir: number): string | undefined => ORDER[ORDER.indexOf(current) + dir];
function showHint(dir: number) {
  const n = neighbour(dir);
  if (!n) { hint.classList.remove('on'); return; }
  hintLabel.textContent = (dir > 0 ? 'Keep scrolling for ' : 'Scroll up for ') + NAMES[n];
  hint.classList.toggle('up', dir < 0);
  hint.classList.add('on');
}
function restHint() {               // resting state: a quiet cue at the end of a page, nothing mid-page
  pull = 0; setPull(0); hint.classList.remove('pulling');
  const v = views[current];
  const atEnd = current === 'home' || v.scrollTop >= maxY(v) - 4;
  if (atEnd && neighbour(1)) showHint(1); else hint.classList.remove('on');
}
let edgeT = 0;
function edge(dir: number, amount: number) {
  const now = performance.now();
  if (now < cooldown || !neighbour(dir)) return;
  if (dir !== pullDir || now - pullT > 500) pull = 0;
  pullDir = dir; pullT = now; pull += amount;
  showHint(dir); hint.classList.add('pulling'); setPull(Math.min(1, pull / PULL));
  clearTimeout(edgeT); edgeT = window.setTimeout(restHint, 650);
  if (pull >= PULL) {
    const n = neighbour(dir);
    pull = 0; cooldown = now + 1300; hint.classList.remove('on', 'pulling');
    const old = views[current];
    cancelAnimationFrame(pullRaf); pullRaf = 0; pullShown = pullTarget = 0; hint.style.setProperty('--p', '0');
    setTimeout(() => { old.style.translate = ''; old.style.opacity = ''; }, 900);   // old page keeps its lift while it fades
    location.hash = n === 'home' ? '#' : '#' + n;
  }
}

subs.forEach(v => v.addEventListener('scroll', () => {
  const s = st(v);
  if (!s.raf || Math.abs(v.scrollTop - s.y) > 3) sync(v);   // scrollbar drag, keyboard or a jump: follow it
  if (v === views[current]) { if (!pull) restHint(); journey(); }
}, { passive: true }));

addEventListener('wheel', e => {
  if (e.ctrlKey) return;                                   // pinch-zoom
  const d = e.deltaY * (e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? innerHeight : 1);
  if (Math.abs(e.deltaX) > Math.abs(d)) return;            // sideways scroll in code blocks
  e.preventDefault();
  if (locked()) {                                          // swallow carry-over momentum from the last page
    const now = performance.now();
    lockUntil = Math.min(lockStart + 2600, Math.max(lockUntil, now + 180));
    return;
  }
  if (current === 'home') { if (d > 0) edge(1, d); return; }
  const v = views[current], s = st(v), m = maxY(v);
  if (d > 0 && s.target >= m - 1 && v.scrollTop >= m - 2) { edge(1, d); return; }
  if (d < 0 && s.target <= 1 && v.scrollTop <= 1) { edge(-1, -d); return; }
  smoothTo(v, s.target + d);
}, { passive: false });

let ty: number | null = null;
addEventListener('touchstart', e => { ty = e.touches[0].clientY; }, { passive: true });
addEventListener('touchmove', e => {
  if (ty == null || locked()) return;
  const y = e.touches[0].clientY, d = ty - y; ty = y;
  const v = views[current];
  const atBottom = current === 'home' || v.scrollTop >= maxY(v) - 2;
  const atTop = current !== 'home' && v.scrollTop <= 0;
  if (d > 0 && atBottom) edge(1, d * 1.8);
  else if (d < 0 && atTop) edge(-1, -d * 1.8);
}, { passive: true });
addEventListener('touchend', () => { ty = null; }, { passive: true });

addEventListener('keydown', e => {
  const target = e.target instanceof Element ? e.target : null;
  if (e.metaKey || e.ctrlKey || e.altKey || target?.closest('input,textarea,select,button,[contenteditable]')) return;
  const down = ['PageDown', ' ', 'ArrowDown'].includes(e.key) && !e.shiftKey;
  const up = ['PageUp', 'ArrowUp'].includes(e.key) || (e.key === ' ' && e.shiftKey);
  if (!down && !up) return;
  if (locked()) { e.preventDefault(); return; }
  const v = views[current];
  const atBottom = current === 'home' || v.scrollTop >= maxY(v) - 2;
  const atTop = current !== 'home' && v.scrollTop <= 1;
  if (down && atBottom) { e.preventDefault(); edge(1, PULL); return; }
  if (up && atTop) { e.preventDefault(); edge(-1, PULL); return; }
  if (current !== 'home') {                                // smooth page/arrow steps too
    e.preventDefault();
    const step = e.key.startsWith('Page') || e.key === ' ' ? v.clientHeight * .85 : 90;
    smoothTo(v, st(v).target + (down ? step : -step));
  }
});

addEventListener('hashchange', () => { lockInput(1000); const v = views[current]; if (v && v !== views.home) { v.scrollTop = 0; sync(v); } journey(); placeDot(); setTimeout(restHint, 700); });
setTimeout(restHint, 1200); journey(); placeDot();

/* ---------- portfolio section nav: the pill follows the section in view ---------- */
const bar = document.querySelector<HTMLElement>('.filters')!, pill = bar.querySelector<HTMLElement>('.pill')!;
const btns = [...bar.querySelectorAll<HTMLButtonElement>('button')];
const pv = views.portfolio;
const active = () => btns.find(b => b.getAttribute('aria-pressed') === 'true');
function placePill(instant: boolean) {
  const b = active(); if (!b) return;
  pill.classList.toggle('instant', instant);
  pill.style.width = b.offsetWidth + 'px'; pill.style.height = b.offsetHeight + 'px';
  pill.style.transform = `translate(${b.offsetLeft}px, ${b.offsetTop}px)`;
  if (instant) { void pill.offsetWidth; pill.classList.remove('instant'); }
}
addEventListener('resize', () => placePill(true));
document.fonts?.ready.then(() => placePill(true));
const setActive = (id: string) => {
  let changed = false;
  btns.forEach(b => { const on = b.dataset.t === id; if ((b.getAttribute('aria-pressed') === 'true') !== on) changed = true; b.setAttribute('aria-pressed', String(on)); });
  if (changed) placePill(false);
};
btns.forEach(btn => btn.addEventListener('click', () => {
  const id = btn.dataset.t!, t = document.getElementById(id)!;
  setActive(id);
  smoothTo(pv, t.offsetTop - 110);
}));
pv.addEventListener('scroll', () => {
  const y = pv.scrollTop + pv.clientHeight * .45;
  setActive(document.getElementById('pf-personal')!.offsetTop <= y ? 'pf-personal' : 'pf-client');
}, { passive: true });
