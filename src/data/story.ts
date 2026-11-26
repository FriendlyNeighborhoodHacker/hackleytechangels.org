export interface Chapter {
  title: string;
  paragraphs: string[];
}

/** Story copy is a starting draft: edit freely to match the club's real history. */
export const chapters: Chapter[] = [
  {
    title: 'The spark',
    paragraphs: [
      'Hackley Tech Angels started with a group of tech-savvy students who wanted to make an impact. They were all fascinated by AI and coding — and by the power of well-done vibe coding to help people quickly and meaningfully.',
    ],
  },
  {
    title: 'How we work',
    paragraphs: [
      'We take great ideas and missions and help make them digitally awesome — making the digital side easier for the people actually working hard to make an impact. Members bring together code, design, hardware and business thinking to take a concept from a sketch on paper to a working application or website that helps people.',
    ],
  },
  {
    title: 'What’s next',
    paragraphs: [
      'More ideas shipped. More students building. More impact. Technology that makes a real difference — at Hackley, in our community and beyond.',
    ],
  },
];
