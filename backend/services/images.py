import base64
import io

from PIL import Image, ImageOps


def decode(b64: str) -> Image.Image:
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    return ImageOps.exif_transpose(img).convert("RGB")
