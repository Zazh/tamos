"""Нормализация загружаемых пользователем изображений: EXIF-rotate,
ресайз до 1024px по длинной стороне, конвертация в JPEG.

Используется в backoffice upload-handler'ах (галереи блога/событий/
доп. страниц/общая галерея) и в `clean_cover_image` соответствующих
форм. PNG-альфа композитится на белый фон.
"""

from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile


MAX_IMAGE_SIDE = 1024
JPEG_QUALITY = 85


def normalize_uploaded_image(uploaded_file):
    """Свежий upload → ContentFile с JPEG. Уже сохранённый FieldFile
    или SVG/повреждённый файл возвращаются без изменений (PIL не
    откроет — оригинал)."""
    if not uploaded_file or not isinstance(uploaded_file, UploadedFile):
        return uploaded_file

    try:
        from PIL import Image, ImageOps
    except ImportError:
        return uploaded_file

    try:
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as im:
            im = ImageOps.exif_transpose(im)
            im = _flatten_alpha(im)
            if max(im.size) > MAX_IMAGE_SIDE:
                im.thumbnail(
                    (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE),
                    Image.Resampling.LANCZOS,
                )
            buf = BytesIO()
            im.save(buf, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return uploaded_file

    orig_name = getattr(uploaded_file, 'name', '') or 'image.jpg'
    base = orig_name.rsplit('/', 1)[-1].rsplit('.', 1)[0] or 'image'
    return ContentFile(buf.getvalue(), name=f'{base}.jpg')


def _flatten_alpha(im):
    from PIL import Image

    if im.mode == 'P':
        im = im.convert('RGBA')
    if im.mode in ('RGBA', 'LA'):
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    if im.mode != 'RGB':
        return im.convert('RGB')
    return im
