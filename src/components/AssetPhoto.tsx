import { useEffect, useState } from 'react';
import { Image, View, type ImageStyle, type StyleProp } from 'react-native';
import * as MediaLibrary from 'expo-media-library/legacy';

// A photo from the phone's library, by asset id. Shows a plain box in `fallbackColor`
// while it loads, or if the id is empty or the photo isn't on this phone.
export function AssetPhoto({
  assetId,
  fallbackColor,
  style,
}: {
  assetId: string;
  fallbackColor: string;
  style: StyleProp<ImageStyle>;
}) {
  const [loaded, setLoaded] = useState<{ id: string; uri: string | null } | null>(null);

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

  const uri = loaded?.id === assetId ? loaded.uri : null;
  if (!uri) return <View style={[style, { backgroundColor: fallbackColor }]} />;
  return <Image source={{ uri }} style={style} resizeMode="cover" onError={() => setLoaded({ id: assetId, uri: null })} />;
}
