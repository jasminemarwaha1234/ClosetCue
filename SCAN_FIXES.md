# Camera-roll scan: fixes to make

From a review of the photo scan in [App.tsx](App.tsx) and [backend/main.py](backend/main.py) on Saturday Oct 17. Work through the fixes in order. The last section lists things that were reviewed and deliberately left as they are, so don't change those.

## 1. Detect body framing with pose keypoints, not box height

**Problem.** `check_sync` in [backend/main.py](backend/main.py) marks a photo `has_outfit` when the tallest person box covers at least 40% of the photo height. A close-up selfie (head and shoulders) passes that test, because the box runs from the top of the head to the bottom of the frame. So do close-ups of anyone else. Nothing in the current test checks that a body, and therefore an outfit, is visible.

**Fix.** Switch from `yolov8n.pt` to the pose model `yolov8n-pose.pt` (same `ultralytics` library, same `predict` call). For each detected person it returns 17 COCO keypoints, each with a confidence score:

| Index | Keypoint |
| --- | --- |
| 0–4 | nose, eyes, ears |
| 5, 6 | left and right shoulder |
| 7–10 | elbows, wrists |
| 11, 12 | left and right hip |
| 13, 14 | left and right knee |
| 15, 16 | left and right ankle |

Classify each person's framing. A keypoint counts as visible when its confidence is at least 0.5.

- **`full`:** upper-body rules pass, and at least one knee and at least one ankle are visible.
- **`upper`:** at least one shoulder and at least one hip are visible.
- **`none`:** anything else, including face-only close-ups.

Return the best framing in the photo (`full` beats `upper` beats `none`, ties broken by the larger box) in a new `framing` field, and set `has_outfit` to `framing != "none"`. Keep a minimum box height, lowered to about 25% of the photo height, so small people in the background don't count. Keep the existing `id`, `has_outfit` and `confidence` fields so the app keeps working, and show `framing` in the app's results if it's quick.

The keypoint scores are in `res.keypoints.conf`, a tensor with one row per person and 17 columns. Box `i` in `res.boxes` is the same person as row `i`.

**Check it works.** Run `check_sync` on at least one photo of each kind below and confirm the result:

| Photo | Expected `framing` |
| --- | --- |
| Close-up selfie, head and shoulders | `none` |
| Waist-up photo | `upper` |
| Full-body mirror selfie | `full` |
| Full-body photo taken by someone else | `full` |
| Landscape with small people far away | `none` |
| No people | `none` |

## 2. Ask only for photo access on Android

`MediaLibrary.usePermissions()` at [App.tsx:72](App.tsx#L72) has no options. On Android 13 and newer that asks for audio and video access as well as photos. Pass `granularPermissions: ['photo']` so the prompt asks only for photos.

## 3. Add a photo-permission message for development builds

Expo Go supplies its own permission text. A development build or a store build shows the text from [app.json](app.json), and without it the build has no explanation of why the app wants photo access. Add the `expo-media-library` config plugin to `app.json` with a `photosPermission` message that says what the app does with photos, for example: "Fitly looks for photos of you in outfits to learn your style. Only small thumbnails leave your phone, and they aren't stored."

## Reviewed and deliberately left as they are

Don't change these. The team decided to keep them for now:

- **Screenshots are skipped.** Keep `looksLikeScreenshot()` as is. Using screenshots as "inspiration" is a later feature.
- **Only the 300 newest photos are scanned.**
- **iCloud-only photos are skipped** (`shouldDownloadFromNetwork: false`).
- **The app uses `expo-media-library/legacy`.** It works; don't migrate it now.
- **The repo stays public and open source**, which is what the AGPL-3.0 license of `ultralytics` and its YOLO weights requires for a network service.
