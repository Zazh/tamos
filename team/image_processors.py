from PIL import Image


class FlattenAlphaToWhite:
    """Кладёт RGBA/палитру с прозрачностью на белый фон.

    Нужно, чтобы PNG с альфой превращался в JPG без чёрных артефактов
    (PIL.convert('RGB') флэтит RGBA на чёрный). На белом школьные портреты
    смотрятся естественнее.
    """

    def process(self, image):
        if image.mode in ('RGBA', 'LA') or (
            image.mode == 'P' and 'transparency' in image.info
        ):
            rgba = image.convert('RGBA')
            background = Image.new('RGB', rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        if image.mode != 'RGB':
            return image.convert('RGB')
        return image
