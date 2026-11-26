import type { ImageMetadata } from 'astro';
import clubzBrowse from '../assets/portfolio/clubz-browse.png';
import clubzClub from '../assets/portfolio/clubz-club.png';
import clubzChat from '../assets/portfolio/clubz-chat.png';
import clubzRsvp from '../assets/portfolio/clubz-rsvp.png';
import pantryHome from '../assets/portfolio/pantry-home.jpg';
import pantryInfo from '../assets/portfolio/pantry-info.jpg';
import bcmSchedule from '../assets/portfolio/bcm-schedule.jpg';
import bcmLesson from '../assets/portfolio/bcm-lesson.jpg';
import bcmLeads from '../assets/portfolio/bcm-leads.jpg';
import bcmLead from '../assets/portfolio/bcm-lead.jpg';
import bcmCalendar from '../assets/portfolio/bcm-calendar.jpg';
import cadence from '../assets/portfolio/cadence.jpg';
import accountable from '../assets/portfolio/accountable.jpg';
import lilly from '../assets/portfolio/lilly.jpg';
import judy from '../assets/portfolio/judy.jpg';
import cutting from '../assets/portfolio/cutting.jpg';
import nail from '../assets/portfolio/nail.jpg';

/** A screenshot. `url` is the text shown in the browser window's address bar. */
export interface Shot {
  src: ImageMetadata;
  alt: string;
  url?: string;
}

export interface ProjectLink {
  label: string;
  href: string;
}

/* ---------- Official work: one full-width case study each ---------- */

export type CaseMedia =
  /** Four phone screens side by side (the last two are hidden on phones). */
  | { kind: 'phones'; shots: Shot[] }
  /** Two overlapping browser windows, plus an optional row of three small ones. */
  | { kind: 'windows'; windows: [Shot, Shot]; thumbs?: Shot[] };

export interface CaseStudy {
  /** Element id: `case-<id>`. */
  id: string;
  kicker: string;
  title: string;
  /** Shown as "Built by <by>". */
  by: string;
  lead: string;
  facts: { label: string; text: string }[];
  skills: string[];
  link: ProjectLink;
  /** Small print next to the button. */
  note: string;
  media: CaseMedia;
}

export const caseStudies: CaseStudy[] = [
  {
    id: 'clubz',
    kicker: 'Hackley School',
    title: 'Hackley Clubz',
    by: 'Lilly',
    lead: 'One place for every club at Hackley. Students browse and join clubs, RSVP to events on a shared calendar and talk in club chats. Faculty approve new clubs and moderate content.',
    facts: [
      { label: 'Sign-in', text: 'Google accounts only, limited to Hackley domains and verified on the server. No passwords to leak.' },
      { label: 'Roles', text: 'Club leaders, club approvers, community-engagement approvers and content moderators each see their own tools.' },
      { label: 'Platforms', text: 'A PHP web app and API, a Python chat server that pushes messages live, and a native Swift iOS app.' },
    ],
    skills: ['PHP', 'Swift / iOS', 'Python', 'MySQL', 'Google Sign-In', 'Security'],
    link: { label: 'Read the docs', href: 'https://docs.hackleyclubz.org/walkthroughs/overview/' },
    note: 'The app is private to Hackley. Screens are from the public walkthrough videos.',
    media: {
      kind: 'phones',
      shots: [
        { src: clubzBrowse, alt: 'Browse Clubs screen listing Abbott House, Debate Club and Waterskiing Club' },
        { src: clubzClub, alt: 'Abbott House club page with mission statement and members' },
        { src: clubzChat, alt: 'Club group chat in the General channel' },
        { src: clubzRsvp, alt: 'RSVP dialog for a club event' },
      ],
    },
  },
  {
    id: 'pantry',
    kicker: 'White Plains, NY',
    title: 'Ecumenical Emergency Food Pantry',
    by: 'Lilly',
    lead: 'A website for a food pantry that serves families every Friday morning. It tells people when to come and who to call, and tells donors exactly what to bring and where to drop it off.',
    facts: [
      { label: 'Get Help', text: 'Serving hours and a phone number up front, for the people who need it most.' },
      { label: 'Donate', text: 'A clear list of the foods and clothing the pantry needs, plus where to send checks.' },
      { label: 'Volunteer', text: 'Thursday set-up and Friday serving shifts, with the pantry’s mission in its own words.' },
    ],
    skills: ['HTML & CSS', 'Responsive design', 'Content writing', 'Information design'],
    link: { label: 'Visit the site', href: 'https://eefoodpantry.org/' },
    note: 'Lilly built it with Milla Reichenberg and Ariella Remus Elliot.',
    media: {
      kind: 'windows',
      windows: [
        { src: pantryHome, url: 'eefoodpantry.org', alt: 'Food pantry home page: Combating Hunger One Family At A Time' },
        { src: pantryInfo, url: 'eefoodpantry.org/volunteer', alt: 'Food pantry information page with volunteer hours' },
      ],
    },
  },
  {
    id: 'bcm',
    kicker: 'Bronx Conservatory of Music',
    title: 'BCM Student Portal',
    by: 'Lilly',
    lead: 'The staff portal that runs a Bronx music school bringing lessons from professional musicians to students at the lowest possible cost. It handles the semester schedule, the weekly calendar, new families and everything in between, so staff stop juggling spreadsheets.',
    facts: [
      { label: 'Schedule', text: 'Every location, teacher and time slot for the semester on one grid, colour-coded by whether each family has paid, owes a balance or is still pending.' },
      { label: 'Leads', text: 'Every public inquiry and registration lands as a lead with its own status, and nothing touches the real roster until staff convert it to a family.' },
      { label: 'Calendar', text: 'Change one week of a lesson: its length, attendance, a substitute teacher or the location, without touching the standing booking.' },
    ],
    skills: ['PHP', 'MySQL', 'Scheduling logic', 'Admin dashboards', 'Authentication'],
    link: { label: 'Read the docs', href: 'https://bcmdocs.lillyrosenthal.org/' },
    note: 'Shown with test data. Lilly built the portal; the conservatory’s main website is by another studio.',
    media: {
      kind: 'windows',
      windows: [
        { src: bcmSchedule, url: 'portal.bronxconservatory.org/schedule', alt: 'Semester schedule for Fall 2026: lessons by teacher and time, colour-coded by payment status' },
        { src: bcmLesson, url: 'portal.bronxconservatory.org/calendar', alt: 'Lesson editor: length, attendance, substitute teacher and location for one week' },
      ],
      thumbs: [
        { src: bcmLeads, url: '…/leads', alt: 'Leads list with status filters and sources' },
        { src: bcmLead, url: '…/leads/aisha-rahman', alt: 'A lead’s inquiry details with a Convert to Family button' },
        { src: bcmCalendar, url: '…/calendar', alt: 'Weekly calendar across two locations' },
      ],
    },
  },
];

/* ---------- Personal projects: a bento grid of cards ---------- */

export type ProjectMedia =
  /** A plain image (already a composed screenshot). */
  | { kind: 'shot'; shot: Shot }
  /** A screenshot inside a browser window; `shot.url` is the address bar. */
  | { kind: 'window'; shot: Shot }
  /** A terminal window. `html` is the screen contents, whitespace preserved; it may use
   *  <span class="pr"> (prompt), <b> (heading), <i> (dim) and <em> (green). */
  | { kind: 'terminal'; title: string; html: string };

export interface PersonalProject {
  /** Card size in the 6-column grid: xl spans 4, tall 2 (media stretches), m 3, s 2,
   *  xs 3 (compact, picture beside the text). Rows should add up to 6. */
  size: 'xl' | 'tall' | 'm' | 's' | 'xs';
  kicker: string;
  title: string;
  /** Shown as "Built by <by>". */
  by: string;
  blurb: string;
  skills: string[];
  link: ProjectLink;
  media: ProjectMedia;
}

export const personalProjects: PersonalProject[] = [
  {
    size: 'xl',
    kicker: 'macOS app',
    title: 'Cadence',
    by: 'Ryan',
    blurb: 'Endless original piano music, composed in real time as you listen. A rules-based composer writes themes, harmonies and counter-melodies bar by bar in four styles, played on a sampled concert grand. An optional rhythmic pulse tuned for focus, relaxation or sleep eases in over the session. Every piece gets its own name and generated cover art, and it all runs offline.',
    skills: ['Swift', 'SwiftUI', 'AVAudioEngine', 'Generative music', '50 tests'],
    link: { label: 'GitHub', href: 'https://github.com/ryanlippman/Cadence' },
    media: {
      kind: 'shot',
      shot: { src: cadence, alt: 'Cadence app window in light and dark mode, playing a piece called Compasses on the Hill' },
    },
  },
  {
    size: 'tall',
    kicker: 'Windows apps on Linux',
    title: 'appbridge',
    by: 'Sophie',
    blurb: 'Runs Microsoft 365, Adobe Creative Cloud and Autodesk apps on Linux. It checks which compatibility tools you have, picks the best way to run each app and adds it to your app menu.',
    skills: ['Python', 'Qt', 'Wine & Proton', 'CLI'],
    link: { label: 'GitHub', href: 'https://github.com/spaley2011/appbridge' },
    media: {
      kind: 'terminal',
      title: 'appbridge',
      html: `<span class="pr">$</span> appbridge list

<b>Microsoft 365</b>
  ○ word        Microsoft Word        not set up
  ○ excel       Microsoft Excel       not set up
  ○ powerpoint  Microsoft PowerPoint  not set up
  ...

<i>● ready  ◐ set up, app not installed  ○ nothing set up</i>`,
    },
  },
  {
    size: 'm',
    kicker: 'Personal site',
    title: 'Lilly Rosenthal',
    by: 'Lilly',
    blurb: 'A portfolio for theatre roles, speeches and tech work, with full-screen photo galleries for each show.',
    skills: ['Web design', 'Galleries'],
    link: { label: 'Visit', href: 'https://www.lillyrosenthal.org/' },
    media: {
      kind: 'window',
      shot: { src: lilly, url: 'lillyrosenthal.org', alt: 'Lilly Rosenthal site showing a stage photo from The Addams Family' },
    },
  },
  {
    size: 'm',
    kicker: 'Any Linux package to Flatpak',
    title: 'debpak',
    by: 'Sophie',
    blurb: 'Turns .deb, .rpm, AppImage, snap and even Windows or Mac Electron apps into Flatpaks. It finds the missing libraries, writes the manifest and can swap every snap for its Flathub version.',
    skills: ['Python', 'Flatpak', 'Packaging', 'Testing'],
    link: { label: 'GitHub', href: 'https://github.com/spaley2011/debpak' },
    media: {
      kind: 'terminal',
      title: 'debpak',
      html: `<span class="pr">$</span> debpak inspect jq_1.7.1_amd64.deb
jq 1.7.1 (amd64, .deb)
  lightweight command-line JSON processor

<b>== Runtime ==</b>
  suggested:  org.freedesktop.Platform//25.08
  needs:      libc.so.6, libjq.so.1

<b>== Verdict ==</b>
  <em>looks convertible</em>`,
    },
  },
  {
    size: 's',
    kicker: 'Family site',
    title: 'Judy Rosenthal',
    by: 'Lilly',
    blurb: 'A home for an artist’s biography, paintings, recipes and family history, presented gallery-style.',
    skills: ['Web design', 'Art gallery'],
    link: { label: 'Visit', href: 'https://judyrosenthal.org/' },
    media: {
      kind: 'window',
      shot: { src: judy, url: 'judyrosenthal.org', alt: 'Judy Rosenthal site showing paintings in a gallery' },
    },
  },
  {
    size: 'xl',
    kicker: 'iPhone & Mac app',
    title: 'Accountable',
    by: 'Ryan',
    blurb: 'A focus app for brains that won’t start on their own. Every session begins with a two-minute starter, the next step is always one tap away, and XP, combos and forgiving streaks reward real focused time. A voice brain dump sorts everything on your mind into tasks with on-device Apple Intelligence. Sessions follow you onto the Lock Screen and into the Dynamic Island.',
    skills: ['Swift', 'SwiftUI', 'WidgetKit', 'Live Activities', 'App Intents', 'Mac Catalyst'],
    link: { label: 'GitHub', href: 'https://github.com/ryanlippman/Accountable' },
    media: {
      kind: 'shot',
      shot: { src: accountable, alt: 'Accountable on iPhone: Today screen with activity rings, Work task list, and a 20-minute focus timer' },
    },
  },
  {
    size: 'xs',
    kicker: 'Local business, Ardsley NY',
    title: 'Cutting Edge Hair Studio',
    by: 'Shaleen',
    blurb: 'A site for a neighborhood salon with its service menu and prices, Google reviews, and one-tap calling and directions.',
    skills: ['Small business', 'Lovable', 'SEO'],
    link: { label: 'Visit', href: 'https://cuttingedgeny.lovable.app/' },
    media: {
      kind: 'window',
      shot: { src: cutting, url: 'cuttingedgeny.lovable.app', alt: 'Cutting Edge Hair Studio home page' },
    },
  },
  {
    size: 'xs',
    kicker: 'Local business, Ardsley NY',
    title: 'Best Nail',
    by: 'Shaleen',
    blurb: 'A warm, simple site for a nail salon: services and starting prices, reviews, and booking by phone.',
    skills: ['Small business', 'Lovable', 'SEO'],
    link: { label: 'Visit', href: 'https://best-nail-bliss.lovable.app/' },
    media: {
      kind: 'window',
      shot: { src: nail, url: 'best-nail-bliss.lovable.app', alt: 'Best Nail salon home page' },
    },
  },
];
