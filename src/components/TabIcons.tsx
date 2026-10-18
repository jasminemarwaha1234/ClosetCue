import type { ColorValue } from 'react-native';
import Svg, { Path, Rect } from 'react-native-svg';

// Tab bar icons, drawn in the same outline style as the Trust screen's. The tab bar passes
// the active or inactive color.

type IconProps = { color: ColorValue; size?: number };

const line = (color: ColorValue) =>
  ({ fill: 'none', stroke: color, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round' }) as const;

// A hanger: your style and closet.
export function StyleIcon({ color, size = 24 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M12 7.5a2 2 0 1 1 2-2" {...line(color)} />
      <Path d="M12 7.5v1.5L3.6 15.2A1.5 1.5 0 0 0 4.5 18h15a1.5 1.5 0 0 0 .9-2.8L12 9" {...line(color)} />
    </Svg>
  );
}

// Sparkles: build an outfit.
export function BuildIcon({ color, size = 24 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M10 4.5l1.6 4.4L16 10.5l-4.4 1.6L10 16.5l-1.6-4.4L4 10.5l4.4-1.6z" {...line(color)} />
      <Path d="M17.5 14.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" {...line(color)} />
    </Svg>
  );
}

// Two outfits side by side: rate which is better.
export function RateIcon({ color, size = 24 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Rect x={3} y={5} width={7.5} height={14} rx={2} {...line(color)} />
      <Rect x={13.5} y={5} width={7.5} height={14} rx={2} {...line(color)} />
    </Svg>
  );
}

// A shield with a check: trust and privacy.
export function TrustIcon({ color, size = 24 }: IconProps) {
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24">
      <Path d="M12 3.5l7 2.6v5.4c0 4.3-2.9 7.6-7 9-4.1-1.4-7-4.7-7-9V6.1z" {...line(color)} />
      <Path d="M9 12l2.2 2.2L15.2 10" {...line(color)} />
    </Svg>
  );
}
