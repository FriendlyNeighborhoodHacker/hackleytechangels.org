/* Hackley Tech Angels — nav, scroll spy, and reveals */
(function () {
  'use strict';

  // Reveal animations only hide content once JS is confirmed running, so the
  // page is never left blank if the script fails or is blocked.
  document.documentElement.classList.add('js');

  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  var navAnchors = links ? links.querySelectorAll('a') : [];

  /* --- Mobile menu --- */
  function closeMenu() {
    links.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open menu');
  }

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });

    // Close after tapping a link on mobile
    navAnchors.forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && links.classList.contains('is-open')) {
        closeMenu();
        toggle.focus();
      }
    });
  }

  /* --- Scroll spy: underline the nav link for the section in view --- */
  var sections = ['projects', 'clubz', 'about', 'contact']
    .map(function (id) { return document.getElementById(id); })
    .filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        navAnchors.forEach(function (a) {
          a.classList.toggle(
            'is-active',
            a.getAttribute('href') === '#' + entry.target.id
          );
        });
      });
    }, {
      // Trigger when a section occupies the middle band of the viewport
      rootMargin: '-45% 0px -50% 0px',
      threshold: 0
    });

    sections.forEach(function (s) { spy.observe(s); });
  }

  /* --- Fade-up reveals --- */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealables = document.querySelectorAll('.reveal');

  if (reduced || !('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-visible'); });
  } else {
    var revealer = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (entry, i) {
        if (!entry.isIntersecting) return;
        // Slight stagger so grids cascade instead of popping at once
        setTimeout(function () {
          entry.target.classList.add('is-visible');
        }, i * 70);
        obs.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });

    revealables.forEach(function (el) { revealer.observe(el); });
  }

  /* --- Footer year --- */
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();
})();
