// import { StatusBar } from 'expo-status-bar';
// import { Link } from 'expo-router';
// import { useRef, useState } from 'react';
// import {
//   ActivityIndicator,
//   Image,
//   Pressable,
//   ScrollView,
//   StyleSheet,
//   Text,
//   View,
// } from 'react-native';
// import * as MediaLibrary from 'expo-media-library/legacy';

// import { classifyBatch, findOwnerCandidates } from '@/api/client';
// import type { Candidate } from '@/api/types';
// import { looksLikeScreenshot, makeThumb, type Thumb } from '@/lib/photos';
// import { colors } from '@/theme';

// // How many of the newest photos to look at.
// const SCAN_LIMIT = 300;
// const BATCH_SIZE = 4; // photos processed at the same time on the phone
// const UPLOAD_BATCH = 10; // thumbnails sent to the backend per request
// const FIND_OWNER_PHOTOS = 80; // newest photos used to find your face

// type Phase = 'idle' | 'scanning' | 'done';
// type Stage = 'shrinking' | 'finding' | 'checking';

// export default function PhotosScreen() {
//   // Android 13+: ask for photos only, not audio and video too.
//   const [permission, requestPermission] = MediaLibrary.usePermissions({
//     granularPermissions: ['photo'],
//   });
//   const [phase, setPhase] = useState<Phase>('idle');
//   const [stage, setStage] = useState<Stage>('shrinking');
//   const [progress, setProgress] = useState({ done: 0, total: 0 });
//   const [outfitThumbs, setOutfitThumbs] = useState<Thumb[]>([]);
//   const [framingCounts, setFramingCounts] = useState({ full: 0, upper: 0 });
//   const [checked, setChecked] = useState(0);
//   const [screenshots, setScreenshots] = useState(0);
//   const [unreadable, setUnreadable] = useState(0);
//   const [limited, setLimited] = useState(false);
//   const [message, setMessage] = useState<string | null>(null);

//   // face matching
//   const [owner, setOwner] = useState<number[] | null>(null);
//   const [candidates, setCandidates] = useState<Candidate[]>([]);
//   const [candIndex, setCandIndex] = useState(0);
//   const [awaitingConfirm, setAwaitingConfirm] = useState(false);
//   const [faceNote, setFaceNote] = useState<string | null>(null);
//   const pending = useRef<((idx: number | null) => void) | null>(null);

//   // Shows the "Is this you?" card and waits for the user to answer.
//   function askUser(cands: Candidate[]): Promise<number | null> {
//     setCandidates(cands);
//     setCandIndex(0);
//     setAwaitingConfirm(true);
//     return new Promise((resolve) => {
//       pending.current = resolve;
//     });
//   }

//   function answer(idx: number | null) {
//     setAwaitingConfirm(false);
//     pending.current?.(idx);
//     pending.current = null;
//   }

//   function onYes() {
//     answer(candIndex);
//   }

//   function onNo() {
//     if (candIndex + 1 < candidates.length) setCandIndex(candIndex + 1);
//     else answer(null);
//   }

//   async function scan() {
//     setMessage(null);
//     setFaceNote(null);
//     setOutfitThumbs([]);
//     setFramingCounts({ full: 0, upper: 0 });
//     setChecked(0);
//     setScreenshots(0);
//     setUnreadable(0);

//     let access = permission;
//     if (!access?.granted) {
//       access = await requestPermission();
//     }
//     if (!access?.granted) {
//       setMessage(
//         'Photo access was not granted. Turn it on in Settings > Expo Go (or this app) > Photos, then try again.'
//       );
//       return;
//     }
//     setLimited(access.accessPrivileges === 'limited');

//     setPhase('scanning');
//     try {
//       const page = await MediaLibrary.getAssetsAsync({
//         first: SCAN_LIMIT,
//         mediaType: 'photo',
//         sortBy: [[MediaLibrary.SortBy.creationTime, false]], // newest first
//       });

//       const usable = page.assets.filter((a) => !looksLikeScreenshot(a));
//       setScreenshots(page.assets.length - usable.length);

//       // Step 1: shrink photos on the phone
//       setStage('shrinking');
//       setProgress({ done: 0, total: usable.length });
//       const made: Thumb[] = [];
//       let failed = 0;
//       for (let i = 0; i < usable.length; i += BATCH_SIZE) {
//         const batch = usable.slice(i, i + BATCH_SIZE);
//         const results = await Promise.all(batch.map(makeThumb));
//         for (const r of results) {
//           if (r) made.push(r);
//           else failed += 1;
//         }
//         setProgress({ done: Math.min(i + BATCH_SIZE, usable.length), total: usable.length });
//       }
//       setUnreadable(failed);
//       setChecked(made.length);

//       // Step 2: find the user's face (first time only), then ask "is this you?"
//       let ownerEmb = owner;
//       if (!ownerEmb) {
//         setStage('finding');
//         const cands = await findOwnerCandidates(made.slice(0, FIND_OWNER_PHOTOS));
//         if (cands.length === 0) {
//           setFaceNote("Couldn't find a face that shows up often, so face matching is off.");
//         } else {
//           const idx = await askUser(cands);
//           if (idx === null) {
//             setFaceNote('Face matching is off because none of the faces were you.');
//           } else {
//             ownerEmb = cands[idx].embedding;
//             setOwner(ownerEmb);
//           }
//         }
//       }

//       // Step 3: send thumbnails to the backend, keep the ones with you in an outfit
//       setStage('checking');
//       setProgress({ done: 0, total: made.length });
//       const byId = new Map(made.map((t) => [t.id, t]));
//       const hits: Thumb[] = [];
//       let full = 0;
//       let upper = 0;
//       for (let i = 0; i < made.length; i += UPLOAD_BATCH) {
//         const found = await classifyBatch(made.slice(i, i + UPLOAD_BATCH), ownerEmb);
//         for (const r of found) {
//           const t = byId.get(r.id);
//           if (!t) continue;
//           hits.push(t);
//           if (r.framing === 'full') full += 1;
//           else if (r.framing === 'upper') upper += 1;
//         }
//         setOutfitThumbs([...hits]);
//         setFramingCounts({ full, upper });
//         setProgress({ done: Math.min(i + UPLOAD_BATCH, made.length), total: made.length });
//       }
//     } catch (e) {
//       setMessage(`Scan failed: ${e instanceof Error ? e.message : String(e)}`);
//     } finally {
//       setAwaitingConfirm(false);
//       setPhase('done');
//     }
//   }

//   const scanning = phase === 'scanning';
//   const pct = progress.total ? Math.round((progress.done / progress.total) * 100) : 0;
//   const stageText =
//     stage === 'shrinking'
//       ? 'Preparing'
//       : stage === 'finding'
//       ? 'Looking for your face in'
//       : 'Finding your outfits in';

//   return (
//     <View style={styles.container}>
//       <ScrollView contentContainerStyle={styles.content}>
//         <Text style={styles.title}>As If</Text>
//         <Text style={styles.subtitle}>Find the photos of you in outfits.</Text>

//         <View style={styles.card}>
//           <Text style={styles.cardTitle}>What this does</Text>
//           <Text style={styles.cardText}>
//             Looks at your {SCAN_LIMIT} newest photos, skips screenshots, and shrinks each one to a
//             small thumbnail. The first time, it finds the face that shows up most and asks if it's
//             you. Then it keeps only photos where you're wearing a visible outfit. Thumbnails are
//             checked on our server and not stored. Full-size photos never leave your phone.
//           </Text>
//         </View>

//         <Pressable
//           onPress={scan}
//           disabled={scanning}
//           style={[styles.button, scanning && styles.buttonDisabled]}
//         >
//           {scanning ? (
//             <ActivityIndicator color={colors.onPrimary} />
//           ) : (
//             <Text style={styles.buttonText}>
//               {phase === 'done' ? 'Scan again' : 'Scan my photos'}
//             </Text>
//           )}
//         </Pressable>

//         {awaitingConfirm && candidates.length > 0 && (
//           <View style={styles.card}>
//             <Text style={styles.cardTitle}>Is this you?</Text>
//             <Image
//               source={{ uri: `data:image/jpeg;base64,${candidates[candIndex].crop}` }}
//               style={styles.faceCrop}
//             />
//             <Text style={styles.cardText}>
//               This face shows up in about {candidates[candIndex].photos} of your recent photos.
//             </Text>
//             <View style={styles.row}>
//               <Pressable onPress={onYes} style={[styles.smallButton, styles.yes]}>
//                 <Text style={styles.buttonText}>Yes, that's me</Text>
//               </Pressable>
//               <Pressable onPress={onNo} style={[styles.smallButton, styles.no]}>
//                 <Text style={styles.noText}>
//                   {candIndex + 1 < candidates.length ? 'Not me' : "None of these"}
//                 </Text>
//               </Pressable>
//             </View>
//           </View>
//         )}

//         {scanning && !awaitingConfirm && (
//           <View style={styles.progressWrap}>
//             <View style={styles.progressTrack}>
//               <View style={[styles.progressFill, { width: `${pct}%` }]} />
//             </View>
//             <Text style={styles.progressText}>
//               {stage === 'finding'
//                 ? 'Looking for your face…'
//                 : `${stageText} ${progress.done} of ${progress.total} photos (${pct}%)`}
//             </Text>
//           </View>
//         )}

//         {message && <Text style={styles.error}>{message}</Text>}
//         {faceNote && <Text style={styles.progressText}>{faceNote}</Text>}

//         {limited && (
//           <View style={styles.notice}>
//             <Text style={styles.noticeText}>
//               You shared only some of your photos. As If works best with more of them.
//             </Text>
//             <Pressable onPress={() => MediaLibrary.presentPermissionsPickerAsync()}>
//               <Text style={styles.link}>Choose more photos</Text>
//             </Pressable>
//           </View>
//         )}

//         {phase === 'done' && (
//           <View style={styles.card}>
//             <Text style={styles.cardTitle}>Results</Text>
//             <Text style={styles.cardText}>Photos with outfits: {outfitThumbs.length}</Text>
//             <Text style={styles.cardText}>Full-body: {framingCounts.full}</Text>
//             <Text style={styles.cardText}>Waist-up: {framingCounts.upper}</Text>
//             <Text style={styles.cardText}>Photos checked: {checked}</Text>
//             <Text style={styles.cardText}>Screenshots skipped: {screenshots}</Text>
//             <Text style={styles.cardText}>Couldn't read (e.g. iCloud only): {unreadable}</Text>
//           </View>
//         )}

//         {owner && !scanning && (
//           <Pressable onPress={() => setOwner(null)}>
//             <Text style={styles.link}>Not you? Reset my face</Text>
//           </Pressable>
//         )}

//         {outfitThumbs.length > 0 && (
//           <View style={styles.grid}>
//             {outfitThumbs.slice(0, 30).map((t) => (
//               <Image
//                 key={t.id}
//                 source={{ uri: `data:image/jpeg;base64,${t.base64}` }}
//                 style={styles.thumb}
//               />
//             ))}
//           </View>
//         )}

//         {phase === 'done' && (
//           <Link href="/style" style={styles.link}>
//             Next: your style
//           </Link>
//         )}
//       </ScrollView>
//       <StatusBar style="auto" />
//     </View>
//   );
// }

// const styles = StyleSheet.create({
//   container: { flex: 1, backgroundColor: colors.background },
//   content: { padding: 24, paddingTop: 72, gap: 16 },
//   title: { fontSize: 28, fontWeight: '700' },
//   subtitle: { fontSize: 15, color: colors.textMuted },
//   card: { backgroundColor: colors.surface, borderRadius: 14, padding: 16, gap: 6 },
//   cardTitle: { fontSize: 16, fontWeight: '600' },
//   cardText: { fontSize: 14, color: colors.textBody },
//   button: {
//     backgroundColor: colors.primary,
//     borderRadius: 14,
//     paddingVertical: 16,
//     alignItems: 'center',
//   },
//   buttonDisabled: { opacity: 0.7 },
//   buttonText: { color: colors.onPrimary, fontSize: 16, fontWeight: '600' },
//   progressWrap: { gap: 6 },
//   progressTrack: { height: 10, backgroundColor: colors.primarySoft, borderRadius: 5, overflow: 'hidden' },
//   progressFill: { height: 10, backgroundColor: colors.primary },
//   progressText: { fontSize: 13, color: colors.textMuted },
//   error: { color: colors.error, fontSize: 14 },
//   notice: { backgroundColor: colors.warningSurface, borderRadius: 14, padding: 14, gap: 6 },
//   noticeText: { fontSize: 14, color: colors.warningText },
//   link: { color: colors.primary, fontWeight: '600' },
//   grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
//   thumb: { width: 96, height: 96, borderRadius: 10, backgroundColor: colors.surfaceMuted },
//   faceCrop: { width: 140, height: 140, borderRadius: 70, alignSelf: 'center', marginVertical: 8 },
//   row: { flexDirection: 'row', gap: 10, marginTop: 8 },
//   smallButton: { flex: 1, borderRadius: 12, paddingVertical: 12, alignItems: 'center' },
//   yes: { backgroundColor: colors.primary },
//   no: { backgroundColor: colors.primarySoft },
//   noText: { color: colors.onPrimarySoft, fontSize: 15, fontWeight: '600' },
// });


import { StatusBar } from 'expo-status-bar';
import { router } from 'expo-router';
import { markOnboarded } from '@/lib/onboarding';
import { getSession } from '@/lib/supabase';
import { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import * as MediaLibrary from 'expo-media-library/legacy';

import { classifyBatch, createProfile, findOwnerCandidates } from '@/api/client';
import type { Candidate } from '@/api/types';
import { looksLikeScreenshot, makeThumb, type Thumb } from '@/lib/photos';
import { useSession } from '@/lib/session';
import { colors, radii, type } from '@/theme';

// How many of the newest photos to look at.
const SCAN_LIMIT = 500;
const BATCH_SIZE = 4; // photos processed at the same time on the phone
const UPLOAD_BATCH = 10; // thumbnails sent to the backend per request
const FIND_OWNER_PHOTOS = 80; // newest photos used to find your face
const PROFILE_PHOTOS = 30; // newest outfit photos sent to POST /profile, its maximum

type Phase = 'idle' | 'scanning' | 'done';
type Stage = 'shrinking' | 'finding' | 'checking';

export default function PhotosScreen() {
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
  const [saving, setSaving] = useState(false);
  const session = useSession();

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

  // Builds and saves the style profile from the outfit photos, then leaves onboarding.
  async function finish() {
    setMessage(null);
    setSaving(true);
    try {
      session.setProfile(await createProfile(outfitThumbs.slice(0, PROFILE_PHOTOS)));
    } catch (e) {
      setMessage(`Couldn't make your style profile: ${e instanceof Error ? e.message : String(e)}`);
      return;
    } finally {
      setSaving(false);
    }
    markOnboarded((await getSession())?.user.id);
    // Onboarding is done, so clear it from the stack: swiping back can't return to it.
    if (router.canDismiss()) router.dismissAll();
    router.replace('/style');
  }

  const scanning = phase === 'scanning';
  const pct = progress.total ? Math.round((progress.done / progress.total) * 100) : 0;
  const stageText =
    stage === 'shrinking'
      ? 'Preparing'
      : stage === 'finding'
      ? 'Looking for your face in'
      : 'Finding your outfits in';

  // Three photo tiles per row, same proportions as the Paper frame (108 x 140).
  const { width } = useWindowDimensions();
  const tileW = Math.floor((width - 48 - 16) / 3);
  const tileH = Math.round(tileW * (140 / 108));

  // Header changes with the phase (Paper frames: Home / Is this you? / Scanning / Results).
  const header = awaitingConfirm
    ? { eyebrow: 'FIRST SCAN', title: 'Is this you?' }
    : scanning
    ? { eyebrow: 'SCANNING', title: 'Finding your outfits' }
    : phase === 'done'
    ? { eyebrow: 'DONE', title: `${outfitThumbs.length} outfit photos` }
    : { eyebrow: 'YOUR PHOTOS', title: 'Find your outfits' };

  const subtitle = awaitingConfirm
    ? candidates.length > 0
      ? `This face shows up in about ${candidates[candIndex].photos} of your recent photos. Confirm it so we only find your outfits.`
      : null
    : scanning
    ? null
    : phase === 'done'
    ? `Checked ${checked} photos and skipped ${screenshots} screenshots.`
    : 'Find the photos of you in outfits.';

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.eyebrow}>{header.eyebrow}</Text>
          <Text style={styles.title}>{header.title}</Text>
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>

        {phase === 'idle' && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>What this does</Text>
            <Text style={styles.cardText}>
              Looks at your {SCAN_LIMIT} newest photos, skips screenshots, and shrinks each one to a
              small thumbnail. The first time, it finds the face that shows up most and asks if it's
              you. Then it keeps only photos where you're wearing a visible outfit. Thumbnails are
              checked on our server and not stored. Full-size photos never leave your phone.
            </Text>
          </View>
        )}

        {awaitingConfirm && candidates.length > 0 && (
          <View style={styles.confirm}>
            <Image
              source={{ uri: `data:image/jpeg;base64,${candidates[candIndex].crop}` }}
              style={styles.faceCrop}
            />
            <View style={styles.answers}>
              <Pressable onPress={onYes} style={styles.button}>
                <Text style={styles.buttonText}>Yes, that's me</Text>
              </Pressable>
              <Pressable onPress={onNo} style={[styles.button, styles.buttonSoft]}>
                <Text style={styles.buttonSoftText}>
                  {candIndex + 1 < candidates.length ? 'Not me' : 'None of these'}
                </Text>
              </Pressable>
            </View>
          </View>
        )}

        {scanning && !awaitingConfirm && (
          <View style={styles.progressWrap}>
            {stage === 'finding' ? (
              <ActivityIndicator color={colors.primary} size="large" style={styles.spinner} />
            ) : (
              <Text style={styles.bigPct}>{pct}%</Text>
            )}
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${pct}%` }]} />
            </View>
            <Text style={styles.subtitle}>
              {stage === 'finding'
                ? 'Looking for your face…'
                : `${stageText} ${progress.done} of ${progress.total} photos`}
            </Text>
          </View>
        )}

        {scanning && !awaitingConfirm && (
          <View style={styles.card}>
            <Text style={styles.cardText}>
              Thumbnails are checked on our server and not stored. Full-size photos never leave
              your phone.
            </Text>
          </View>
        )}

        {message && <Text style={styles.error}>{message}</Text>}
        {faceNote && <Text style={styles.subtitle}>{faceNote}</Text>}

        {limited && (
          <View style={styles.notice}>
            <Text style={styles.noticeText}>
              You shared only some of your photos. As If works best with more of them.
            </Text>
            <Pressable onPress={() => MediaLibrary.presentPermissionsPickerAsync()}>
              <Text style={styles.link}>Choose more photos</Text>
            </Pressable>
          </View>
        )}

        {phase === 'done' && (
          <View style={styles.stats}>
            <View style={styles.stat}>
              <Text style={styles.statNumber}>{framingCounts.full}</Text>
              <Text style={styles.statLabel}>Full body</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statNumber}>{framingCounts.upper}</Text>
              <Text style={styles.statLabel}>Waist up</Text>
            </View>
          </View>
        )}

        {phase === 'done' && unreadable > 0 && (
          <Text style={styles.subtitle}>
            Couldn't read {unreadable} (e.g. iCloud only).
          </Text>
        )}

        {outfitThumbs.length > 0 && (
          <View style={styles.grid}>
              {outfitThumbs.map((t) => (
              <Image
                key={t.id}
                source={{ uri: `data:image/jpeg;base64,${t.base64}` }}
                style={[styles.thumb, { width: tileW, height: tileH }]}
              />
            ))}
          </View>
        )}

        {(phase === 'idle' || phase === 'done') && (
          <Pressable onPress={scan} style={styles.button}>
            <Text style={styles.buttonText}>{phase === 'done' ? 'Scan again' : 'Scan my photos'}</Text>
          </Pressable>
        )}

        {owner && !scanning && (
          <Pressable onPress={() => setOwner(null)} style={styles.linkRow}>
            <Text style={styles.linkMuted}>Not you? Reset my face</Text>
          </Pressable>
        )}

        {phase === 'done' && (
          <Text
            accessibilityRole="link"
            onPress={saving ? undefined : finish}
            style={[styles.link, styles.linkCenter]}
          >
            {saving ? 'Reading your style…' : 'Next: your style'}
          </Text>
        )}
      </ScrollView>
      <StatusBar style="dark" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 24, paddingTop: 72, paddingBottom: 40, gap: 24 },

  header: { gap: 12 },
  eyebrow: { ...type.eyebrow, color: colors.primary },
  title: { ...type.display, color: colors.text },
  subtitle: { ...type.lead, color: colors.textMuted },

  card: { backgroundColor: colors.surface, borderRadius: radii.xl, padding: 20, gap: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600', lineHeight: 22, color: colors.text },
  cardText: { fontSize: 15, lineHeight: 22, color: colors.textBody },

  button: {
    height: 56,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: { ...type.button, color: colors.onPrimary },
  buttonSoft: { backgroundColor: colors.primarySoft },
  buttonSoftText: { ...type.button, color: colors.onPrimarySoft },

  confirm: { gap: 32, alignItems: 'stretch' },
  faceCrop: {
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 4,
    borderColor: colors.primary,
    backgroundColor: colors.surface,
    alignSelf: 'center',
  },
  answers: { gap: 12 },

  progressWrap: { gap: 20 },
  bigPct: { ...type.hero, color: colors.primary },
  spinner: { alignSelf: 'flex-start', height: 96, justifyContent: 'center' },
  progressTrack: {
    height: 12,
    backgroundColor: colors.primarySoft,
    borderRadius: 6,
    overflow: 'hidden',
  },
  progressFill: { height: 12, backgroundColor: colors.primary, borderRadius: 6 },

  error: { color: colors.error, fontSize: 14 },
  notice: { backgroundColor: colors.warningSurface, borderRadius: radii.xl, padding: 16, gap: 6 },
  noticeText: { fontSize: 14, color: colors.warningText },

  stats: { flexDirection: 'row', gap: 12 },
  stat: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radii.xl,
    paddingVertical: 16,
    paddingHorizontal: 20,
    gap: 2,
  },
  statNumber: { ...type.stat, color: colors.primary },
  statLabel: { fontSize: 15, lineHeight: 20, color: colors.textBody },

  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  thumb: { borderRadius: radii.lg, backgroundColor: colors.surfaceMuted },

  link: { color: colors.primary, fontWeight: '600', fontSize: 16 },
  linkCenter: { textAlign: 'center' },
  linkRow: { height: 44, alignItems: 'center', justifyContent: 'center' },
  linkMuted: { color: colors.textMuted, fontSize: 15, fontWeight: '500' },
});