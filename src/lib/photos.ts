import * as MediaLibrary from 'expo-media-library/legacy';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';

const THUMB_WIDTH = 512; // bigger than before so faces are readable
const THUMB_QUALITY = 0.6;

export type Thumb = { id: string; base64: string; takenAt: number };

export function looksLikeScreenshot(asset: MediaLibrary.Asset): boolean {
  if (asset.mediaSubtypes?.includes('screenshot')) return true; // iOS
  return /screenshot/i.test(asset.filename); // Android and others
}

// Shrinks one photo on the phone. Returns null if the photo can't be read
// (for example, iCloud photos that aren't downloaded to the phone).
export async function makeThumb(asset: MediaLibrary.Asset): Promise<Thumb | null> {
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

// Shrinks a picked photo for try-on. Bigger than a thumbnail so the result looks good.
export async function shrinkForTryOn(uri: string): Promise<string | null> {
  try {
    const context = ImageManipulator.manipulate(uri);
    context.resize({ width: 768 });
    const image = await context.renderAsync();
    const result = await image.saveAsync({ format: SaveFormat.JPEG, compress: 0.7, base64: true });
    return result.base64 ?? null;
  } catch {
    return null;
  }
}
