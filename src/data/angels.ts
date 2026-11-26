import type { ImageMetadata } from 'astro';
import angel1 from '../assets/angels/angel-1.png';
import angel2 from '../assets/angels/angel-2.png';
import angel3 from '../assets/angels/angel-3.png';
import angel4 from '../assets/angels/angel-4.png';

export interface Angel {
  name: string;
  /** Line under the name. "Tech Angel" is a placeholder: replace with each member's real title. */
  role: string;
  /** Cut-out portrait (transparent PNG) in src/assets/angels/. */
  portrait: ImageMetadata;
  /** Portrait placement inside the card, as CSS values:
   *  height (% of card), bottom (% up from the card's bottom edge), offsetX (% right of centre),
   *  haloX (where the head is, % from the left). */
  fit: { height: string; bottom: string; offsetX: string; haloX: string };
  /** Which part of the sky painting is behind the portrait, and how it is tinted. */
  art: { position: string; hue: string; saturation: number };
}

export const angels: Angel[] = [
  {
    name: 'Lilly',
    role: 'Tech Angel',
    portrait: angel1,
    fit: { height: '70.9%', bottom: '4.1%', offsetX: '-4.5%', haloX: '50.7%' },
    art: { position: '15% 30%', hue: '-18deg', saturation: 1.15 },
  },
  {
    name: 'Ryan',
    role: 'Tech Angel',
    portrait: angel2,
    fit: { height: '52.9%', bottom: '22.8%', offsetX: '0.8%', haloX: '49.7%' },
    art: { position: '70% 45%', hue: '200deg', saturation: 1.05 },
  },
  {
    name: 'Shaleen',
    role: 'Tech Angel',
    portrait: angel3,
    fit: { height: '67.3%', bottom: '9.3%', offsetX: '-3.5%', haloX: '48.7%' },
    art: { position: '45% 75%', hue: '18deg', saturation: 1.12 },
  },
  {
    name: 'Sophie',
    role: 'Tech Angel',
    portrait: angel4,
    fit: { height: '64.4%', bottom: '14.9%', offsetX: '9.4%', haloX: '54.2%' },
    art: { position: '85% 20%', hue: '-34deg', saturation: 1.1 },
  },
];
