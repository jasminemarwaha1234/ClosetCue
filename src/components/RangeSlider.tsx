import { useMemo, useState } from 'react';
import { PanResponder, StyleSheet, View, type GestureResponderEvent } from 'react-native';

import { colors } from '@/theme';

const THUMB = 24;

// The stop at or just below a value, so values that aren't stops still place the handle.
const indexOf = (stops: number[], v: number) => Math.max(stops.findLastIndex((s) => s <= v), 0);

// A slider with two handles for a min-max range. Built on PanResponder, so it runs in Expo Go.
// The whole track takes the touch: the handle nearest the finger follows it. The handles snap
// to `stops`, spaced evenly on the track, so small budgets get fine steps and large ones big jumps.
export function RangeSlider({
  stops,
  value,
  onChange,
}: {
  stops: number[];
  value: [number, number];
  onChange: (v: [number, number]) => void;
}) {
  const [width, setWidth] = useState(0);
  const [active, setActive] = useState<0 | 1 | null>(null);

  const last = stops.length - 1;
  const span = Math.max(width - THUMB, 1);
  const low = indexOf(stops, value[0]);
  const high = indexOf(stops, value[1]);
  const toX = (index: number) => (index / last) * span;

  const responder = useMemo(() => {
    const indexAt = (e: GestureResponderEvent) => {
      const x = Math.min(Math.max(e.nativeEvent.locationX - THUMB / 2, 0), span);
      return Math.round((x / span) * last);
    };
    const move = (handle: 0 | 1, raw: number) => {
      const next = handle === 0 ? Math.max(Math.min(raw, high - 1), 0) : Math.min(Math.max(raw, low + 1), last);
      if (next !== (handle === 0 ? low : high)) {
        onChange(handle === 0 ? [stops[next], value[1]] : [value[0], stops[next]]);
      }
    };
    const nearest = (raw: number): 0 | 1 => (Math.abs(raw - low) <= Math.abs(raw - high) ? 0 : 1);

    return PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: (e) => {
        const raw = indexAt(e);
        const handle = nearest(raw);
        setActive(handle);
        move(handle, raw);
      },
      onPanResponderMove: (e) => {
        const raw = indexAt(e);
        move(active ?? nearest(raw), raw);
      },
      onPanResponderRelease: () => setActive(null),
      onPanResponderTerminate: () => setActive(null),
    });
  }, [value, stops, last, low, high, span, onChange, active]);

  const lowX = toX(low);
  const highX = toX(high);

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
