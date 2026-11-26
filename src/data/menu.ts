export interface MenuItem {
  /** Label in the nav bar. */
  name: string;
  /** The view's element id and URL hash (#portfolio). */
  route: string;
  /** Browser-tab title and the name used in the "Keep scrolling for …" cue. */
  title: string;
}

/** Nav order, which is also the order the pages scroll through after Home.
 *  The logo (Home) sits in the middle of the bar. Each route needs a matching
 *  <section id={route} class="view sub"> in src/pages/index.astro. */
export const menu: MenuItem[] = [
  { name: 'Portfolio', route: 'portfolio', title: 'Portfolio' },
  { name: 'Angels', route: 'angels', title: 'The Angels' },
  { name: 'Story', route: 'story', title: 'Our Story' },
  { name: 'Contact', route: 'contact', title: 'Contact' },
];
