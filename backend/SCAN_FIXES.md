# Camera-roll scan: fixes

From a review of the photo scan on Saturday Oct 17. The code now lives in [photos.tsx](../src/app/onboarding/photos.tsx) on the app side, and in [services/pose.py](services/pose.py) (`check_sync`) and [services/faces.py](services/faces.py) (`find_owner_sync`) on the backend. Fixes 1–3 are done; fix 4 is open. The last section lists things that were reviewed and deliberately left as they are, so don't change those.

| Fix | Status |
| --- | --- |
| 1. Detect body framing with pose keypoints, not box height | Done in `159d03b` |
| 2. Ask only for photo access on Android (`granularPermissions: ['photo']`) | Done in `159d03b` |
| 3. Add the `expo-media-library` photo-permission message to [app.json](../app.json) | Done in `159d03b` |
| 4. Make the models safe to share between requests, and batch the pose model | Open |

## 1. Detect body framing with pose keypoints (done)

The old check marked a photo as an outfit when the tallest person box covered 40% of the photo height, so close-up selfies passed. `check_sync` now uses the pose model `yolov8n-pose.pt`, which scores 17 COCO keypoints per person:

| Index | Keypoint |
| --- | --- |
| 0–4 | nose, eyes, ears |
| 5, 6 | left and right shoulder |
| 7–10 | elbows, wrists |
| 11, 12 | left and right hip |
| 13, 14 | left and right knee |
| 15, 16 | left and right ankle |

A keypoint counts as visible when its confidence is at least 0.5. Each person's framing is:

- **`full`:** upper-body rules pass, and at least one knee and at least one ankle are visible.
- **`upper`:** at least one shoulder and at least one hip are visible.
- **`none`:** anything else, including face-only close-ups.

People shorter than 25% of the photo height don't count. The photo gets the best framing (`full` beats `upper`, ties broken by the larger box), and `has_outfit` is `framing != "none"`. The commit added two rules beyond the original fix: with no owner face set, photos with more than 3 people are skipped (`MAX_PEOPLE`), and with an owner face set, only people whose face matches count.

**Check it works.** From the repo root, run `python -m backend.test_framing <photo> …` on at least one photo of each kind below:

| Photo | Expected `framing` |
| --- | --- |
| Close-up selfie, head and shoulders | `none` |
| Waist-up photo | `upper` |
| Full-body mirror selfie | `full` |
| Full-body photo taken by someone else | `full` |
| Landscape with small people far away | `none` |
| No people | `none` |

## 4. Make the models safe to share between requests, and batch the pose model

**Problem.** Both routes run on their own threads (`asyncio.to_thread`), and every thread uses the same three global models: `pose_model` (YOLO), `mtcnn` (face finder) and `resnet` (face embeddings). Ultralytics warns that its predictor isn't thread-safe, so two phones scanning at once can collide in `pose_model.predict`. The face models are plain PyTorch models in inference mode, which are generally safe to call from several threads, but they compete for the same CPU. `check_sync` also calls `pose_model.predict` once per image, which is slower than one call for the whole batch.

**Fix.**

- Add one module-level `threading.Lock()` and hold it around all model work: the `pose_model.predict` call, and `detect_faces` in both `check_sync` and `find_owner_sync`. One lock is simpler than one per model, and it costs almost no speed, because one CPU does the work either way.
- In `/scan`, decode every image in the request first, then call `pose_model.predict(images, ...)` once with the list. Result `i` belongs to image `i`. Keep the per-image error handling: an image that fails to decode gets `has_outfit: False`, `framing: "none"` and an `error` field, and is left out of the `predict` list. Face matching stays per image, after the pose step, and only for photos that still have a candidate person.
- Keep the work inside `asyncio.to_thread`. Calling the models directly in the async handler would block the whole server, so `/health` and every other request would wait.

**Check it works.**

- Send two `/scan` requests at the same time, for example with two `curl` commands started together. Both must return correct results with no errors, and the results must match what each request returns when sent alone.
- Do the same with one `/scan` and one `/faces/find-owner` request at the same time.
- Run `test_framing.py` on the photos from fix 1 and confirm the framings haven't changed.

## Reviewed and deliberately left as they are

Don't change these. The team decided to keep them for now:

- **Screenshots are skipped.** Keep `looksLikeScreenshot()` as is. Using screenshots as "inspiration" is a later feature.
- **Only the 500 newest photos are scanned.**
- **iCloud-only photos are skipped** (`shouldDownloadFromNetwork: false`).
- **The app uses `expo-media-library/legacy`.** It works; don't migrate it now.
- **The repo stays public and open source**, which is what the AGPL-3.0 license of `ultralytics` and its YOLO weights requires for a network service.
