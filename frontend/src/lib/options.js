export const GENRES = [
  'Dark Fantasy', 'Fantasy', 'Sci-Fi', 'Mystery', 'Adventure',
  'Romance', 'Horror', 'Slice of Life', 'Thriller', 'Comedy',
]

/** Tone presets map to the 0-100 tone dial sent to the backend (0 = dark, 100 = light). */
export const TONES = [
  { label: 'Grim', value: 10 },
  { label: 'Mysterious', value: 30 },
  { label: 'Bittersweet', value: 50 },
  { label: 'Hopeful', value: 70 },
  { label: 'Whimsical', value: 90 },
]

export const nearestTone = (v) =>
  TONES.reduce((best, t) => (Math.abs(t.value - v) < Math.abs(best.value - v) ? t : best), TONES[0]).value

export const STRATEGY_LABELS = {
  direct: 'Direct prompting',
  interview: 'Interview Pattern',
  cot: 'Chain-of-Thought',
  tot: 'Tree-of-Thought',
}

export const STRATEGY_STEPS = {
  direct: ['Writing the story'],
  interview: ['Interviewing the idea', 'Writing the story'],
  cot: ['Planning world, characters and arc', 'Writing the story'],
  tot: ['Exploring three plot branches', 'Scoring and selecting a branch', 'Writing the story'],
}

export const EMPTY_IDEA = { protagonist: '', goal: '', genre: 'Dark Fantasy', world_rule: '', ending_twist: '' }

/** Starter ideas shown on Explore. They prefill the Create form; nothing here is pre-generated. */
export const STARTER_IDEAS = [
  {
    title: 'The Shattered Veil', art: 'idea-the-shattered-veil', genre: 'Dark Fantasy', hue: 265,
    pitch: 'A fallen world. A forgotten power. A price for every spell.',
    idea: {
      protagonist: 'A lone exorcist with forgotten powers', goal: 'Uncover the truth behind a shattered world',
      world_rule: 'Magic exists, but every spell costs the caster a memory',
      ending_twist: "The real villain is the protagonist's future self",
    },
    plot: { tone: 30, conflict: 80, romance: 30, action: 85, length: 60 }, strategy: 'tot',
  },
  {
    title: 'Neon Requiem', art: 'idea-neon-requiem', genre: 'Sci-Fi', hue: 210,
    pitch: 'A dreaming machine searches for a colony erased from history.',
    idea: {
      protagonist: 'A teenage repair robot who has just gained the ability to dream',
      goal: 'Find out who erased the last human colony on Mars from every record',
      world_rule: 'Machines are forbidden from keeping memories longer than seven days',
      ending_twist: 'The robot itself erased the colony to protect the humans',
    },
    plot: { tone: 50, conflict: 60, romance: 10, action: 40, length: 50 }, strategy: 'cot',
  },
  {
    title: 'The Cherry Blossom Café', art: 'idea-the-cherry-blossom-cafe', genre: 'Slice of Life', hue: 330,
    pitch: 'A café, a quiet gift, and a festival deadline.',
    idea: {
      protagonist: "A shy café owner who can hear what people's coffee orders really mean",
      goal: 'Save the café from closing before the cherry blossom festival',
      world_rule: 'The gift only works on strangers, never on people she loves',
      ending_twist: 'The rival café owner was her childhood pen pal all along',
    },
    plot: { tone: 90, conflict: 30, romance: 90, action: 10, length: 40 }, strategy: 'interview',
  },
  {
    title: 'The Last Lantern', art: 'idea-the-last-lantern', genre: 'Mystery', hue: 35,
    pitch: 'When the last lantern goes out, the town forgets its name.',
    idea: {
      protagonist: 'A night-watch apprentice who keeps the town lanterns burning',
      goal: 'Find who is stealing the lantern flames one by one',
      world_rule: 'Anyone outside the lantern light by midnight is forgotten by everyone',
      ending_twist: 'The thief is trying to free the town from the lanterns, not destroy it',
    },
    plot: { tone: 30, conflict: 60, romance: 20, action: 40, length: 60 }, strategy: 'cot',
  },
  {
    title: 'Echoes of the Deep', art: 'idea-echoes-of-the-deep', genre: 'Adventure', hue: 190,
    pitch: 'A diver follows a song from beneath a drowned city.',
    idea: {
      protagonist: 'A pearl diver who can hold her breath for an hour',
      goal: 'Reach the drowned capital and find the source of a mysterious song',
      world_rule: 'The sea returns every object it takes, but never in the same form',
      ending_twist: 'The song is her own voice, recorded before she was born',
    },
    plot: { tone: 70, conflict: 50, romance: 30, action: 70, length: 60 }, strategy: 'direct',
  },
  {
    title: 'Room 404', art: 'idea-room-404', genre: 'Horror', hue: 0,
    pitch: 'A hotel room that only appears to people who are lost.',
    idea: {
      protagonist: 'A night-shift receptionist at a hotel with 403 rooms',
      goal: 'Find out why guests keep checking into Room 404',
      world_rule: 'The hotel rearranges itself every night at 3 a.m.',
      ending_twist: 'The receptionist has been a guest of Room 404 for years',
    },
    plot: { tone: 10, conflict: 70, romance: 0, action: 30, length: 40 }, strategy: 'interview',
  },
  {
    title: 'Two Moons Apart', art: 'idea-two-moons-apart', genre: 'Romance', hue: 290,
    pitch: 'Two letter-writers on worlds that meet once a decade.',
    idea: {
      protagonist: 'A lighthouse keeper on a planet with two moons',
      goal: 'Meet the stranger she has written letters to for ten years',
      world_rule: 'Letters can only cross between the worlds during an eclipse',
      ending_twist: 'They have already met once, as children, and both forgot',
    },
    plot: { tone: 70, conflict: 30, romance: 95, action: 10, length: 50 }, strategy: 'direct',
  },
  {
    title: 'The Heist of Hours', art: 'idea-the-heist-of-hours', genre: 'Thriller', hue: 150,
    pitch: 'A crew plans to rob a bank that stores time.',
    idea: {
      protagonist: 'A disgraced clockmaker turned thief',
      goal: 'Steal back the ten years the Time Bank took from her sister',
      world_rule: 'Time can be deposited, loaned and stolen, but never created',
      ending_twist: 'Her sister sold those years willingly to pay for the heist',
    },
    plot: { tone: 40, conflict: 85, romance: 20, action: 80, length: 60 }, strategy: 'tot',
  },
  {
    title: "The Dragon's Apprentice", art: 'idea-the-dragons-apprentice', genre: 'Fantasy', hue: 25,
    pitch: 'A clumsy apprentice, the last dragon, and a kingdom it once burned.',
    idea: {
      protagonist: 'A clumsy apprentice who can understand the language of dragons',
      goal: 'Convince the last dragon to save the kingdom it once burned',
      world_rule: 'Dragons can only speak to people who have never told a lie',
      ending_twist: "The apprentice is the dragon's lost child in human form",
    },
    plot: { tone: 70, conflict: 55, romance: 20, action: 60, length: 60 }, strategy: 'interview',
  },
  {
    title: "The Wizard's Lost Socks", art: 'idea-the-wizards-lost-socks', genre: 'Comedy', hue: 285,
    pitch: 'A sarcastic cat, a forgetful wizard and a very important pair of socks.',
    idea: {
      protagonist: "A sarcastic cat who works as an overworked wizard's familiar",
      goal: "Recover the wizard's enchanted socks before the royal ball",
      world_rule: 'Every spell has a fifty percent chance of doing the exact opposite',
      ending_twist: 'The socks ran away on purpose to start a band',
    },
    plot: { tone: 95, conflict: 40, romance: 10, action: 40, length: 40 }, strategy: 'direct',
  },
]
