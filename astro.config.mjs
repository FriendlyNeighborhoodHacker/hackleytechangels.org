// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
// Pure static build (no server adapter needed — the host has no Node).
export default defineConfig({
  output: 'static',
});
