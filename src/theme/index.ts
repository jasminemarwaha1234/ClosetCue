// // Design tokens from the Paper style guide. Values are seeded from the current screens until the guide is done.

// export const colors = {
//   background: '#fff',
//   surface: '#f6f4fb',
//   surfaceMuted: '#eee',
//   primary: '#7c4dff',
//   primarySoft: '#e5e0f5',
//   onPrimary: '#fff',
//   onPrimarySoft: '#4a3a8a',
//   text: '#000',
//   textBody: '#333',
//   textMuted: '#555',
//   error: '#c0392b',
//   warningSurface: '#fff6e5',
//   warningText: '#6b4e00',
// } as const;

// export const spacing = {
//   xs: 6,
//   sm: 12,
//   md: 16,
//   lg: 24,
// } as const;

// export const radii = {
//   sm: 10,
//   md: 12,
//   lg: 14,
// } as const;

// export const type = {
//   title: { fontSize: 28, fontWeight: '700' },
//   heading: { fontSize: 16, fontWeight: '600' },
//   body: { fontSize: 15 },
//   small: { fontSize: 14 },
//   caption: { fontSize: 13 },
// } as const;
// Design tokens from the Paper style guide ("Jolly cloud" file, Fitly / As If screens).
// Existing keys keep their names so other screens keep working; values now match Paper.

export const colors = {
  background: '#ffffff',
  surface: '#f3eeff', // lavender cards
  surfaceMuted: '#ebe3ff', // photo tiles, empty states
  primary: '#7c4dff', // amethyst accent
  primarySoft: '#f3eeff', // secondary buttons, progress track
  onPrimary: '#ffffff',
  onPrimarySoft: '#5b2fd6',
  text: '#17132b', // ink
  textBody: '#4a4466',
  textMuted: '#6b6585',
  hairline: '#e4dcfa',
  error: '#c0392b',
  warningSurface: '#fff6e5',
  warningText: '#6b4e00',
} as const;

export const spacing = {
  xs: 6,
  sm: 12,
  md: 16,
  lg: 24,
} as const;

export const radii = {
  sm: 10,
  md: 12,
  lg: 14, // photo tiles
  xl: 20, // cards
  pill: 28, // buttons
} as const;

export const type = {
  // Paper scale
  wordmark: { fontSize: 64, fontWeight: '800', letterSpacing: -2.5, lineHeight: 64 },
  hero: { fontSize: 96, fontWeight: '800', letterSpacing: -4.8, lineHeight: 96 },
  display: { fontSize: 44, fontWeight: '800', letterSpacing: -1.5, lineHeight: 48 },
  stat: { fontSize: 32, fontWeight: '800', letterSpacing: -1, lineHeight: 36 },
  eyebrow: { fontSize: 14, fontWeight: '600', letterSpacing: 1.1 },
  lead: { fontSize: 17, lineHeight: 24 },
  button: { fontSize: 17, fontWeight: '600' },
  // Existing scale (kept for screens that haven't moved over yet)
  title: { fontSize: 28, fontWeight: '700' },
  heading: { fontSize: 16, fontWeight: '600' },
  body: { fontSize: 15 },
  small: { fontSize: 14 },
  caption: { fontSize: 13 },
} as const;