# hackleytechangels.org

The Hackley Tech Angels site: a student club's portfolio, members, story and
contact form. An [Astro](https://astro.build) static site (plus one small PHP
endpoint for the contact form), following the same conventions as
judyrosenthal.com and lillyrosenthal.com.

## Run it

```sh
npm install
npm run dev            # http://localhost:4321
npm run build          # static site in dist/
npm run preview        # serve dist/
```

Node 22.12 or newer.

## How it is put together

The whole site is one page, `src/pages/index.astro`, with five full-screen
views: Home, Portfolio, Angels, Story, Contact. `src/scripts/site.ts` switches
between them on the URL hash (`/#portfolio`), which is what lets the painted
sky and the doves carry across from page to page. Scrolling past the end of a
page moves on to the next one.

| Path | What it controls |
| --- | --- |
| `src/data/menu.ts` | Nav labels, page order, browser-tab titles. |
| `src/data/portfolio.ts` | "Official work" case studies and "Personal projects" cards: text, links, skills, screenshots, card sizes. |
| `src/data/angels.ts` | Members: name, role line, cut-out portrait and where it sits in the card. |
| `src/data/story.ts` | The Story page's chapters. |
| `src/data/siteConfig.ts` | Site name and description, footer Instagram / Website links, contact endpoint. |
| `src/components/` | One component per view (`Home`, `Portfolio`, `Angels`, `Story`, `Contact`) plus shared pieces (`Nav`, `Footer`, `Backdrop`, `PageHead`, `Band`, `BrowserWindow`, `Terminal`, `Arrow`, `LogoDefs`). |
| `src/styles/global.css` | All styles. |
| `src/scripts/` | `site.ts` (routing, scrolling), `nixie.ts` (neon title), `glass.ts` (glass refraction), `contact.ts` (form). |
| `src/assets/` | Images. Screenshots and portraits are converted to WebP at build time. |
| `public/` | Files copied to the web root as they are: favicon, `CREDITS.md`, and the PHP files below. |

To add a project: put its screenshot in `src/assets/portfolio/`, import it at
the top of `src/data/portfolio.ts` and add an entry to `caseStudies` or
`personalProjects`. To add a member: a transparent PNG in `src/assets/angels/`
and an entry in `src/data/angels.ts`.

Still placeholders: each member's role line ("Tech Angel"), the story text,
the footer's Instagram and Website links (`siteConfig.ts`) and the "Terms &
Policies" link.

## Contact form

The form posts to `public/contact.php`, which checks the fields and emails the
message through an SMTP account (`public/mailer.php`, no dependencies) to the
address in `CONTACT_TO`. The visitor's address goes in Reply-To. Nothing is
stored. Once it is sent the visitor lands on a thank-you view (`/#thanks`,
`src/components/Thanks.astro`) with a link back to the home page. A hidden honeypot field and a limit of 5 messages per IP per hour keep
bots down.

The SMTP account and the recipient are in `config.local.php` on the server
(template: `public/config.local.php.example`; same `SMTP_*` constant names as
portal.bronxconservatory.org and neon.everosenthal.com). Until they are filled
in, the form tells visitors the inbox is not connected yet.

`npm run dev` has no PHP, so the form reports a failure there. To try it
locally:

```sh
npm run build
cp public/config.local.php.example dist/config.local.php   # fill in SMTP_* and CONTACT_TO
php -S localhost:8080 -t dist
```

## Deploying

A push to `main` on GitHub (`FriendlyNeighborhoodHacker/hackleytechangels.org`)
rebuilds the site: `gitwebhook.php` verifies the push and runs the deploy
script, which builds the checkout and swaps the result into the web root.

Layout on the server, all under the site user's home:

| Path | Purpose |
| --- | --- |
| `~/deploy/hackleytechangels.org/` | git checkout; built here, never served |
| `~/deploy/hackleytechangels.org.sh` | the deploy script the webhook runs: a copy of `deploy/hackleytechangels.org.sh` kept outside the checkout, so a deploy cannot change the script under its own feet |
| `~/deploy/hackleytechangels.org.secrets/config.local.php` | webhook secret, SMTP account, contact recipient (master copy; each deploy installs it into the web root) |
| `~/deploy/hackleytechangels.org.deploy.log` | webhook + deploy output |
| `~/hackleytechangels.org/` | web root; replaced on every deploy, previous build kept in `~/hackleytechangels.org.old/` |

The script derives every path from `$HOME`; export `SITE_HOME`, `REPO_DIR`,
`SECRETS_DIR`, `WEB_ROOT`, `BRANCH` or `NODE_VERSION` to override.

### One-time setup

As the site user. Needs nvm with Node 22 at `~/.nvm`, plus git and php on the
PATH.

```sh
mkdir -p ~/deploy/hackleytechangels.org.secrets && chmod 700 ~/deploy/hackleytechangels.org.secrets
git clone git@github.com:FriendlyNeighborhoodHacker/hackleytechangels.org.git ~/deploy/hackleytechangels.org
cp ~/deploy/hackleytechangels.org/deploy/hackleytechangels.org.sh ~/deploy/hackleytechangels.org.sh
cp ~/deploy/hackleytechangels.org/public/config.local.php.example ~/deploy/hackleytechangels.org.secrets/config.local.php
chmod 600 ~/deploy/hackleytechangels.org.secrets/config.local.php
# edit it: WEBHOOK_SECRET, DEPLOY_SCRIPT and DEPLOY_LOG (real home directory), SMTP_*, CONTACT_TO
bash ~/deploy/hackleytechangels.org.sh
```

Then point the Apache vhost at `~/hackleytechangels.org` (PHP enabled,
`AllowOverride All` so `.htaccess` can deny `config.local.php` and
`mailer.php`), and in GitHub → repo → Settings → Webhooks set the payload URL
to `https://hackleytechangels.org/gitwebhook.php`, content type
`application/json`, Secret = `WEBHOOK_SECRET`, "Just the push event".

After changing `deploy/hackleytechangels.org.sh`, refresh the server's copy:

```sh
cp ~/deploy/hackleytechangels.org/deploy/hackleytechangels.org.sh ~/deploy/hackleytechangels.org.sh
```

### Moving over from the old site

The previous site in this repository was plain HTML served straight from a
checkout, with the deploy script at
`~/deploy_scripts/hackleytechangels.org.deploy.sh` and an array-style
`config.local.php` (`return ['webhook_secret' => ...]`). Three things change:

- `config.local.php` now uses `define()` constants. Start from the new
  template and carry the old webhook secret over as `WEBHOOK_SECRET`, so the
  existing GitHub webhook keeps working.
- The web root is no longer a git checkout; it is replaced by the build on
  every deploy. Do the one-time setup above, which leaves the old web root in
  `~/hackleytechangels.org.old/`.
- Replacing the repository's history means the server needs a fresh clone
  (the setup above), not a `git pull` in the old checkout.

### Uptime monitor

`https://hackleytechangels.org/uptime.php` returns `200` with a body starting
`success : <timestamp>` when PHP runs and the web root holds a complete
`index.html`, and `503` with `failure : <timestamp> : <reason>` otherwise.
