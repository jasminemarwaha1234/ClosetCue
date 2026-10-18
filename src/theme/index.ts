// Design tokens from the Paper style guide. Values are seeded from the current screens until the guide is done.

export const colors = {
  background: '#fff',
  surface: '#f6f4fb',
  surfaceMuted: '#eee',
  primary: '#7c4dff',
  primarySoft: '#e5e0f5',
  onPrimary: '#fff',
  onPrimarySoft: '#4a3a8a',
  text: '#000',
  textBody: '#333',
  textMuted: '#555',
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
  lg: 14,
} as const;

export const type = {
  title: { fontSize: 28, fontWeight: '700' },
  heading: { fontSize: 16, fontWeight: '600' },
  body: { fontSize: 15 },
  small: { fontSize: 14 },
  caption: { fontSize: 13 },
} as const;
