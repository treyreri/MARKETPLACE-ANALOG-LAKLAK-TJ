import uuid
from pathlib import Path
from fastapi import UploadFile

PRODUCT_IMAGE_DIR = Path("uploads") / "products"
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp", }
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


class InvalidImageError(Exception):
    pass


def save_product_image(file: UploadFile) -> str:
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise InvalidImageError("Only JPEG, PNG and WEBP images are allowed")

    content = file.file.read(MAX_IMAGE_SIZE + 1)
    if len(content) > MAX_IMAGE_SIZE:
        raise InvalidImageError("Image must be smaller than 5 MB")

    PRODUCT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    path = PRODUCT_IMAGE_DIR / f"{uuid.uuid4().hex}{extension}"
    path.write_bytes(content)
    return path.as_posix()


def delete_file(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


#Мы никогда не используем имя файла от пользователя, только UUID. 
#Так защищаемся от путей вроде ../../app/main.py. content_type присылает клиент, его можно подделать