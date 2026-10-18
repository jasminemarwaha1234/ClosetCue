import Svg, { Path } from 'react-native-svg';

// Brand marks for the payment picker. These colors are the brands' own, so they
// don't come from the theme.

export function AppleLogo({ size = 14, color = '#ffffff' }: { size?: number; color?: string }) {
  return (
    <Svg width={size * 0.85} height={size} viewBox="0 0 17 20">
      <Path
        fill={color}
        d="M14.1 10.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9C3.6 4.8 1.9 5.9 1 7.5c-1.9 3.3-.5 8.1 1.3 10.8.9 1.3 2 2.7 3.4 2.7 1.4-.1 1.9-.9 3.5-.9s2.1.9 3.5.9c1.4 0 2.4-1.3 3.2-2.6 1-1.5 1.4-2.9 1.4-3-.1 0-2.9-1.1-3.2-4.8zM11.5 2.9c.7-.9 1.2-2.1 1.1-3.3-1 0-2.3.7-3 1.6-.7.8-1.2 2-1.1 3.2 1.1.1 2.3-.6 3-1.5z"
      />
    </Svg>
  );
}
