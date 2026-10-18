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
// Design tokens from the Paper style guide ("Jolly cloud" file, Fitly / ClosetCue screens).
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
  errorSurface: '#fdecea', // refused cart
  errorTrack: '#f6cfca',
  errorText: '#8c2a1f',
  ink: '#17132b', // selected filter chip
  dashed: '#c9b8ff', // closet pieces, add buttons
  scrim: 'rgba(23, 19, 43, 0.42)', // behind sheets
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

// Hex for each color name the backend uses (CatalogItem.colors, ClosetItem.colors).
// Shown when an item has no image. Unknown names fall back to surfaceMuted.
export const swatches: Record<string, string> = {
  cream: '#efe4cc',
  white: '#ffffff',
  black: '#1b1b1b',
  gray: '#9a9aa0',
  grey: '#9a9aa0',
  charcoal: '#3a3a40',
  navy: '#202848',
  blue: '#3b5ba5',
  'light-blue': '#a9c7e8',
  denim: '#4a6890',
  olive: '#6e7445',
  green: '#4f7a4a',
  'muted-green': '#8a9a7b',
  'forest-green': '#2f5233',
  tan: '#c8a67e',
  beige: '#d9c8a9',
  khaki: '#b8a77a',
  brown: '#6b4a32',
  burgundy: '#6d2233',
  red: '#b3312c',
  pink: '#e8a5b8',
  lilac: '#d9ccfa',
  purple: '#7c4dff',
  yellow: '#e8c547',
  orange: '#d9772b',
  gold: '#c9a54c',
  silver: '#c0c0c8',
};

// Payment brands' own colors, for the payment picker's marks.
export const brands = {
  applePay: '#000000',
  visa: '#1a1f71',
  paypal: '#ffc439',
  paypalText: '#003087',
} as const;

export const type = {
  // Paper scale
  wordmark: { fontSize: 64, fontWeight: '800', letterSpacing: -2.5, lineHeight: 64 },
  hero: { fontSize: 96, fontWeight: '800', letterSpacing: -4.8, lineHeight: 96 },
  display: { fontSize: 44, fontWeight: '800', letterSpacing: -1.5, lineHeight: 48 },
  title: { fontSize: 36, fontWeight: '800', letterSpacing: -1.26, lineHeight: 40 }, // screen titles
  section: { fontSize: 20, fontWeight: '700', letterSpacing: -0.2, lineHeight: 24 },
  stat: { fontSize: 32, fontWeight: '800', letterSpacing: -1, lineHeight: 36 },
  eyebrow: { fontSize: 14, fontWeight: '600', letterSpacing: 1.1 },
  lead: { fontSize: 17, lineHeight: 24 },
  button: { fontSize: 17, fontWeight: '600' },
  // Existing scale (kept for screens that haven't moved over yet)
  heading: { fontSize: 16, fontWeight: '600' },
  body: { fontSize: 15 },
  small: { fontSize: 14 },
  caption: { fontSize: 13 },
} as const;