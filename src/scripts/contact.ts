/* Contact form: validates, then posts to public/contact.php, which emails the message
   through the SMTP account in the server's config.local.php. On success it shows the
   thank-you view (#thanks, src/components/Thanks.astro). */
import { siteConfig } from '../data/siteConfig';

const form = document.querySelector<HTMLFormElement>('.form')!, status = form.querySelector<HTMLElement>('.status')!;
const button = form.querySelector<HTMLButtonElement>('button[type=submit]')!;
const say = (msg: string) => { status.textContent = msg; status.classList.remove('show'); void status.offsetWidth; status.classList.add('show'); };
const validEmail = (s: string) => /^\S+@\S+\.\S+$/.test(s);

const ERRORS: Record<string, string> = {
  invalid: 'Please add your name, a valid email and a short message.',
  rate: 'That’s a lot of messages — please try again in an hour.',
  unconfigured: 'Our inbox isn’t connected yet — please reach us on Instagram for now.',
};
const FAILED = 'Sorry, that didn’t send. Please try again in a moment.';

let sending = false;
form.addEventListener('submit', async e => {
  e.preventDefault();
  if (sending) return;
  const data = new FormData(form);
  const field = (name: string) => String(data.get(name) ?? '');
  const name = field('name'), email = field('email'), message = field('message');
  if (!name.trim() || !validEmail(email) || !message.trim()) {
    say(ERRORS.invalid);
    form.querySelector<HTMLElement>(!name.trim() ? '[name=name]' : !validEmail(email) ? '[name=email]' : '[name=message]')?.focus();
    return;
  }
  sending = true; button.disabled = true;
  say('Sending…');
  try {
    const res = await fetch(siteConfig.contactEndpoint, { method: 'POST', body: data });
    const out: { ok?: boolean; error?: string } = await res.json();
    if (out.ok) {
      // on to the thank-you view; the form is cleared behind it so coming back starts fresh
      form.reset(); status.textContent = ''; status.classList.remove('show');
      location.hash = '#thanks';
    } else say(ERRORS[out.error ?? ''] ?? FAILED);
  } catch {
    // no PHP behind `astro dev` / `astro preview`, or the network dropped
    say(FAILED);
  } finally {
    sending = false; button.disabled = false;
  }
});
