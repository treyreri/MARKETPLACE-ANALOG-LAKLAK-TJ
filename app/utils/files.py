import io
import uuid
from pathlib import Path
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

PRODUCT_IMAGE_DIR = Path("uploads") / "products"
# Pillow format name -> file extension. The client's content_type is ignored:
# it is just a header and can be anything.
ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp", }
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


class InvalidImageError(Exception):
    pass


def _detect_image_format(content: bytes) -> str:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image_format = image.format
            image.verify()  # checks structure/checksums without decoding all pixels
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError):
        raise InvalidImageError("File is not a valid JPEG, PNG or WEBP image")
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise InvalidImageError("Only JPEG, PNG and WEBP images are allowed")
    return image_format


def save_product_image(file: UploadFile) -> str:
    content = file.file.read(MAX_IMAGE_SIZE + 1)
    if len(content) > MAX_IMAGE_SIZE:
        raise InvalidImageError("Image must be smaller than 5 MB")

    extension = ALLOWED_IMAGE_FORMATS[_detect_image_format(content)]
    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    path = PRODUCT_IMAGE_DIR / f"{uuid.uuid4().hex}{extension}"
    path.write_bytes(content)
    return path.as_posix()


def delete_file(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


# The client's filename is never used, only a UUID, which protects against
# paths like ../../app/main.py. The extension comes from the detected format.
