import { StatusBar } from 'expo-status-bar';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import * as MediaLibrary from 'expo-media-library/legacy';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';

// How many of the newest photos to look at, and how small to shrink each one.
const SCAN_LIMIT = 300;
const THUMB_WIDTH = 512; // bigger than before so faces are readable
const THUMB_QUALITY = 0.6;
const BATCH_SIZE = 4; // photos processed at the same time on the phone
const UPLOAD_BATCH = 10; // thumbnails sent to the backend per request
const FIND_OWNER_PHOTOS = 80; // newest photos used to find your face

// Set in .env as EXPO_PUBLIC_API_BASE_URL (use your laptop's LAN IP on a real phone)
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type Thumb = { id: string; base64: string; takenAt: number };
type Phase = 'idle' | 'scanning' | 'done';
type Stage = 'shrinking' | 'finding' | 'checking';
type Framing = 'full' | 'upper' | 'none';
type ScanResult = { id: string; has_outfit: boolean; framing?: Framing; confidence?: number };
type Candidate = { embedding: number[]; crop: string; photos: number };

function looksLikeScreenshot(asset: MediaLibrary.Asset): boolean {
  if (asset.mediaSubtypes?.includes('screenshot')) return true; // iOS
  return /screenshot/i.test(asset.filename); // Android and others
}

// Shrinks one photo on the phone. Returns null if the photo can't be read
// (for example, iCloud photos that aren't downloaded to the phone).
async function makeThumb(asset: MediaLibrary.Asset): Promise<Thumb | null> {
  try {
    const info = await MediaLibrary.getAssetInfoAsync(asset, {
      shouldDownloadFromNetwork: false,
    });
    const uri = info.localUri ?? asset.uri;
    const context = ImageManipulator.manipulate(uri);
    context.resize({ width: THUMB_WIDTH });
    const image = await context.renderAsync();
    const result = await image.saveAsync({
      format: SaveFormat.JPEG,
      compress: THUMB_QUALITY,
      base64: true,
    });
    return result.base64
      ? { id: asset.id, base64: result.base64, takenAt: asset.creationTime }
      : null;
  } catch {
    return null;
  }
}

// Asks the backend for the most common faces in these photos.
async function findOwnerCandidates(thumbs: Thumb[]): Promise<Candidate[]> {
  const res = await fetch(`${API_BASE_URL}/faces/find-owner`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(thumbs.map(({ id, base64 }) => ({ id, base64 }))),
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  const data: { candidates: Candidate[] } = await res.json();
  return data.candidates;
}

// Sends one batch of thumbnails to the backend and returns the results that have an outfit.
async function classifyBatch(batch: Thumb[], owner: number[] | null): Promise<ScanResult[]> {
  const res = await fetch(`${API_BASE_URL}/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items: batch.map(({ id, base64 }) => ({ id, base64 })),
      owner_embedding: owner,
    }),
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  const data: { results: ScanResult[] } = await res.json();
  return data.results.filter((r) => r.has_outfit);
}

export default function App() {
  // Android 13+: ask for photos only, not audio and video too.
  const [permission, requestPermission] = MediaLibrary.usePermissions({
    granularPermissions: ['photo'],
  });
  const [phase, setPhase] = useState<Phase>('idle');
  const [stage, setStage] = useState<Stage>('shrinking');
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [outfitThumbs, setOutfitThumbs] = useState<Thumb[]>([]);
  const [framingCounts, setFramingCounts] = useState({ full: 0, upper: 0 });
  const [checked, setChecked] = useState(0);
  const [screenshots, setScreenshots] = useState(0);
  const [unreadable, setUnreadable] = useState(0);
  const [limited, setLimited] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // face matching
  const [owner, setOwner] = useState<number[] | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [candIndex, setCandIndex] = useState(0);
  const [awaitingConfirm, setAwaitingConfirm] = useState(false);
  const [faceNote, setFaceNote] = useState<string | null>(null);
  const pending = useRef<((idx: number | null) => void) | null>(null);

  // Shows the "Is this you?" card and waits for the user to answer.
  function askUser(cands: Candidate[]): Promise<number | null> {
    setCandidates(cands);
    setCandIndex(0);
    setAwaitingConfirm(true);
    return new Promise((resolve) => {
      pending.current = resolve;
    });
  }

  function answer(idx: number | null) {
    setAwaitingConfirm(false);
    pending.current?.(idx);
    pending.current = null;
  }

  function onYes() {
    answer(candIndex);
  }

  function onNo() {
    if (candIndex + 1 < candidates.length) setCandIndex(candIndex + 1);
    else answer(null);
  }

  async function scan() {
    setMessage(null);
    setFaceNote(null);
    setOutfitThumbs([]);
    setFramingCounts({ full: 0, upper: 0 });
    setChecked(0);
    setScreenshots(0);
    setUnreadable(0);

    let access = permission;
    if (!access?.granted) {
      access = await requestPermission();
    }
    if (!access?.granted) {
      setMessage(
        'Photo access was not granted. Turn it on in Settings > Expo Go (or this app) > Photos, then try again.'
      );
      return;
    }
    setLimited(access.accessPrivileges === 'limited');

    setPhase('scanning');
    try {
      const page = await MediaLibrary.getAssetsAsync({
        first: SCAN_LIMIT,
        mediaType: 'photo',
        sortBy: [[MediaLibrary.SortBy.creationTime, false]], // newest first
      });

      const usable = page.assets.filter((a) => !looksLikeScreenshot(a));
      setScreenshots(page.assets.length - usable.length);

      // Step 1: shrink photos on the phone
      setStage('shrinking');
      setProgress({ done: 0, total: usable.length });
      const made: Thumb[] = [];
      let failed = 0;
      for (let i = 0; i < usable.length; i += BATCH_SIZE) {
        const batch = usable.slice(i, i + BATCH_SIZE);
        const results = await Promise.all(batch.map(makeThumb));
        for (const r of results) {
          if (r) made.push(r);
          else failed += 1;
        }
        setProgress({ done: Math.min(i + BATCH_SIZE, usable.length), total: usable.length });
      }
      setUnreadable(failed);
      setChecked(made.length);

      // Step 2: find the user's face (first time only), then ask "is this you?"
      let ownerEmb = owner;
      if (!ownerEmb) {
        setStage('finding');
        const cands = await findOwnerCandidates(made.slice(0, FIND_OWNER_PHOTOS));
        if (cands.length === 0) {
          setFaceNote("Couldn't find a face that shows up often, so face matching is off.");
        } else {
          const idx = await askUser(cands);
          if (idx === null) {
            setFaceNote('Face matching is off because none of the faces were you.');
          } else {
            ownerEmb = cands[idx].embedding;
            setOwner(ownerEmb);
          }
        }
      }

      // Step 3: send thumbnails to the backend, keep the ones with you in an outfit
      setStage('checking');
      setProgress({ done: 0, total: made.length });
      const byId = new Map(made.map((t) => [t.id, t]));
      const hits: Thumb[] = [];
      let full = 0;
      let upper = 0;
      for (let i = 0; i < made.length; i += UPLOAD_BATCH) {
        const found = await classifyBatch(made.slice(i, i + UPLOAD_BATCH), ownerEmb);
        for (const r of found) {
          const t = byId.get(r.id);
          if (!t) continue;
          hits.push(t);
          if (r.framing === 'full') full += 1;
          else if (r.framing === 'upper') upper += 1;
        }
        setOutfitThumbs([...hits]);
        setFramingCounts({ full, upper });
        setProgress({ done: Math.min(i + UPLOAD_BATCH, made.length), total: made.length });
      }
    } catch (e) {
      setMessage(`Scan failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setAwaitingConfirm(false);
      setPhase('done');
    }
  }

  const scanning = phase === 'scanning';
  const pct = progress.total ? Math.round((progress.done / progress.total) * 100) : 0;
  const stageText =
    stage === 'shrinking'
      ? 'Preparing'
      : stage === 'finding'
      ? 'Looking for your face in'
      : 'Finding your outfits in';

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Fitly</Text>
        <Text style={styles.subtitle}>Find the photos of you in outfits.</Text>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>What this does</Text>
          <Text style={styles.cardText}>
            Looks at your {SCAN_LIMIT} newest photos, skips screenshots, and shrinks each one to a
            small thumbnail. The first time, it finds the face that shows up most and asks if it's
            you. Then it keeps only photos where you're wearing a visible outfit. Thumbnails are
            checked on our server and not stored. Full-size photos never leave your phone.
          </Text>
        </View>

        <Pressable
          onPress={scan}
          disabled={scanning}
          style={[styles.button, scanning && styles.buttonDisabled]}
        >
          {scanning ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>
              {phase === 'done' ? 'Scan again' : 'Scan my photos'}
            </Text>
          )}
        </Pressable>

        {awaitingConfirm && candidates.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Is this you?</Text>
            <Image
              source={{ uri: `data:image/jpeg;base64,${candidates[candIndex].crop}` }}
              style={styles.faceCrop}
            />
            <Text style={styles.cardText}>
              This face shows up in about {candidates[candIndex].photos} of your recent photos.
            </Text>
            <View style={styles.row}>
              <Pressable onPress={onYes} style={[styles.smallButton, styles.yes]}>
                <Text style={styles.buttonText}>Yes, that's me</Text>
              </Pressable>
              <Pressable onPress={onNo} style={[styles.smallButton, styles.no]}>
                <Text style={styles.noText}>
                  {candIndex + 1 < candidates.length ? 'Not me' : "None of these"}
                </Text>
              </Pressable>
            </View>
          </View>
        )}

        {scanning && !awaitingConfirm && (
          <View style={styles.progressWrap}>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${pct}%` }]} />
            </View>
            <Text style={styles.progressText}>
              {stage === 'finding'
                ? 'Looking for your face…'
                : `${stageText} ${progress.done} of ${progress.total} photos (${pct}%)`}
            </Text>
          </View>
        )}

        {message && <Text style={styles.error}>{message}</Text>}
        {faceNote && <Text style={styles.progressText}>{faceNote}</Text>}

        {limited && (
          <View style={styles.notice}>
            <Text style={styles.noticeText}>
              You shared only some of your photos. Fitly works best with more of them.
            </Text>
            <Pressable onPress={() => MediaLibrary.presentPermissionsPickerAsync()}>
              <Text style={styles.link}>Choose more photos</Text>
            </Pressable>
          </View>
        )}

        {phase === 'done' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Results</Text>
            <Text style={styles.cardText}>Photos with outfits: {outfitThumbs.length}</Text>
            <Text style={styles.cardText}>Full-body: {framingCounts.full}</Text>
            <Text style={styles.cardText}>Waist-up: {framingCounts.upper}</Text>
            <Text style={styles.cardText}>Photos checked: {checked}</Text>
            <Text style={styles.cardText}>Screenshots skipped: {screenshots}</Text>
            <Text style={styles.cardText}>Couldn't read (e.g. iCloud only): {unreadable}</Text>
          </View>
        )}

        {owner && !scanning && (
          <Pressable onPress={() => setOwner(null)}>
            <Text style={styles.link}>Not you? Reset my face</Text>
          </Pressable>
        )}

        {outfitThumbs.length > 0 && (
          <View style={styles.grid}>
            {outfitThumbs.slice(0, 30).map((t) => (
              <Image
                key={t.id}
                source={{ uri: `data:image/jpeg;base64,${t.base64}` }}
                style={styles.thumb}
              />
            ))}
          </View>
        )}
      </ScrollView>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  content: { padding: 24, paddingTop: 72, gap: 16 },
  title: { fontSize: 28, fontWeight: '700' },
  subtitle: { fontSize: 15, color: '#555' },
  card: { backgroundColor: '#f6f4fb', borderRadius: 14, padding: 16, gap: 6 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardText: { fontSize: 14, color: '#333' },
  button: {
    backgroundColor: '#7c4dff',
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
  },
  buttonDisabled: { opacity: 0.7 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  progressWrap: { gap: 6 },
  progressTrack: { height: 10, backgroundColor: '#e5e0f5', borderRadius: 5, overflow: 'hidden' },
  progressFill: { height: 10, backgroundColor: '#7c4dff' },
  progressText: { fontSize: 13, color: '#555' },
  error: { color: '#c0392b', fontSize: 14 },
  notice: { backgroundColor: '#fff6e5', borderRadius: 14, padding: 14, gap: 6 },
  noticeText: { fontSize: 14, color: '#6b4e00' },
  link: { color: '#7c4dff', fontWeight: '600' },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  thumb: { width: 96, height: 96, borderRadius: 10, backgroundColor: '#eee' },
  faceCrop: { width: 140, height: 140, borderRadius: 70, alignSelf: 'center', marginVertical: 8 },
  row: { flexDirection: 'row', gap: 10, marginTop: 8 },
  smallButton: { flex: 1, borderRadius: 12, paddingVertical: 12, alignItems: 'center' },
  yes: { backgroundColor: '#7c4dff' },
  no: { backgroundColor: '#e5e0f5' },
  noText: { color: '#4a3a8a', fontSize: 15, fontWeight: '600' },
});