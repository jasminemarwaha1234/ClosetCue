import { useMemo, useState } from 'react';
import { PanResponder, StyleSheet, View, type GestureResponderEvent } from 'react-native';

import { colors } from '@/theme';

const THUMB = 24;

// A slider with two handles for a min-max range. Built on PanResponder, so it runs in Expo Go.
// The whole track takes the touch: the handle nearest the finger follows it.
export function RangeSlider({
  min,
  max,
  step,
  value,
  onChange,
}: {
  min: number;
  max: number;
  step: number;
  value: [number, number];
  onChange: (v: [number, number]) => void;
}) {
  const [width, setWidth] = useState(0);
  const [active, setActive] = useState<0 | 1 | null>(null);

  const span = Math.max(width - THUMB, 1);
  const toX = (v: number) => ((v - min) / (max - min)) * span;

  const responder = useMemo(() => {
    const valueAt = (e: GestureResponderEvent) => {
      const x = Math.min(Math.max(e.nativeEvent.locationX - THUMB / 2, 0), span);
      return Math.round((min + (x / span) * (max - min)) / step) * step;
    };
    const move = (handle: 0 | 1, raw: number) => {
      let next = handle === 0 ? Math.min(raw, value[1] - step) : Math.max(raw, value[0] + step);
      next = Math.min(Math.max(next, min), max);
      if (next !== value[handle]) onChange(handle === 0 ? [next, value[1]] : [value[0], next]);
    };
    const nearest = (raw: number): 0 | 1 =>
      Math.abs(raw - value[0]) <= Math.abs(raw - value[1]) ? 0 : 1;

    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: (e) => {
        const raw = valueAt(e);
        const handle = nearest(raw);
        setActive(handle);
        move(handle, raw);
      },
      onPanResponderMove: (e) => {
        const raw = valueAt(e);
        move(active ?? nearest(raw), raw);
      },
      onPanResponderRelease: () => setActive(null),
      onPanResponderTerminate: () => setActive(null),
    });
  }, [value, min, max, step, span, onChange, active]);

  const lowX = toX(value[0]);
  const highX = toX(value[1]);

  return (
    <View
      style={styles.root}
      onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
      hitSlop={{ top: 12, bottom: 12 }}
      accessibilityLabel={`Budget from $${value[0]} to $${value[1]}`}
      {...responder.panHandlers}
    >
      {/* Children ignore touches so locationX is always relative to the track. */}
      <View pointerEvents="none" style={StyleSheet.absoluteFill}>
        <View style={styles.track} />
        <View style={[styles.fill, { left: lowX + THUMB / 2, width: highX - lowX }]} />
        <View style={[styles.thumb, { left: lowX }]} />
        <View style={[styles.thumb, { left: highX }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { height: THUMB },
  track: {
    position: 'absolute',
    top: (THUMB - 6) / 2,
    left: THUMB / 2,
    right: THUMB / 2,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.hairline,
  },
  fill: {
    position: 'absolute',
    top: (THUMB - 6) / 2,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary,
  },
  thumb: {
    position: 'absolute',
    top: 0,
    width: THUMB,
    height: THUMB,
    borderRadius: THUMB / 2,
    borderWidth: 3,
    borderColor: colors.primary,
    backgroundColor: colors.background,
  },
});
