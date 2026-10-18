import { useEffect, useState } from 'react';
import { Image, View, type ImageStyle, type StyleProp } from 'react-native';
import * as MediaLibrary from 'expo-media-library/legacy';

// The local uri of a photo in the phone's library, by asset id. Null while it loads,
// or if the id is empty or the photo isn't on this phone.
export function useAssetUri(assetId: string | undefined): string | null {
  const [loaded, setLoaded] = useState<{ id: string; uri: string } | null>(null);

  useEffect(() => {
    if (!assetId) return;
    let live = true;
    MediaLibrary.getAssetInfoAsync(assetId, { shouldDownloadFromNetwork: false })
      .then((info) => {
        if (live) setLoaded({ id: assetId, uri: info.localUri ?? info.uri });
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [assetId]);

  return loaded && loaded.id === assetId ? loaded.uri : null;
}

// A photo from the phone's library, or a plain box in `fallbackColor` without one.
export function AssetPhoto({
  assetId,
  fallbackColor,
  style,
}: {
  assetId: string;
  fallbackColor: string;
  style: StyleProp<ImageStyle>;
}) {
  const uri = useAssetUri(assetId);
  const [failed, setFailed] = useState<string | null>(null);

  if (!uri || failed === uri) return <View style={[style, { backgroundColor: fallbackColor }]} />;
  return <Image source={{ uri }} style={style} resizeMode="cover" onError={() => setFailed(uri)} />;
}
