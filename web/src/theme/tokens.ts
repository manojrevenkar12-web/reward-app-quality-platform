/**
 * Tokens for the reward-app quality dashboard. A pale lilac-grey ground like a phone's settings screen at night
 * mode's edge, deep violet ink, and one magenta for focus and the active view: the colour of a "reward" badge, kept
 * away from the data. Series use the validated first three categorical slots (all pairs pass colour-blind
 * checks): blue the platform, orange the app as found, aqua "automate everything", grey the ablations. How
 * escaped defects were found uses five slots with a legend and the counts in a table. Status words always come
 * with a colour, never a colour alone.
 */
export const color = {
  ground: "#F3F2F7",
  sheet: "#FFFFFF",
  ink: "#1C1830",
  copy: "#2E2A40",
  muted: "#5A5670",
  line: "#DAD7E3",
  focus: "#A21C5A",
  good: "#15663F",
  goodWash: "#DDF0E5",
  warn: "#8A5300",
  warnWash: "#FBEFD9",
  bad: "#B42318",
  badWash: "#FBE4E1",
  platform: "#2a78d6",
  asFound: "#eb6834",
  everything: "#1baf7a",
  ablation: "#A3A9A6",
  platformInk: "#1C5CAB",
  asFoundInk: "#A8410F",
  everythingInk: "#0E6B49",
  part1: "#2a78d6",
  part2: "#eb6834",
  part3: "#1baf7a",
  part4: "#eda100",
  part5: "#e87ba4",
} as const;

export const font = {
  ui: ["Bricolage Grotesque Variable", "Bricolage Grotesque", "system-ui", "sans-serif"],
  code: ["IBM Plex Mono", "ui-monospace", "monospace"],
} as const;

/** 1.25 ratio from a 15px base. [size, line-height] */
export const type = {
  small: ["0.8125rem", "1.4"],
  body: ["0.9375rem", "1.55"],
  lead: ["1.1875rem", "1.4"],
  title: ["1.875rem", "1.15"],
  hero: ["2.75rem", "1.05"],
} as const;

export const space = { 0: "0", 1: "0.25rem", 2: "0.5rem", 3: "0.75rem", 4: "1rem", 5: "1.5rem", 6: "2rem", 7: "3rem", 8: "4rem" } as const;
export const radius = { none: "0", soft: "6px", card: "14px", pill: "999px" } as const;
export const measure = { prose: "66ch", page: "78rem", hero: "54rem", table: "56rem" } as const;
export const line = { hair: "1px", rule: "2px" } as const;
export const size = { swatch: "0.625rem", bar: "1.5rem", label: "13rem" } as const;
