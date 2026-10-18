import base64
import io
import sys

from PIL import Image, ImageOps

from backend.schemas import Item
from backend.services.pose import check_sync

for path in sys.argv[1:]:
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    img.thumbnail((256, 10**6))  # same size the app sends
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=60)
    b64 = base64.b64encode(buf.getvalue()).decode()
    out = check_sync(Item(id=path, base64=b64))
    print(f"{path}: framing={out['framing']} has_outfit={out['has_outfit']} conf={out['confidence']:.2f}")