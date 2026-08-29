from PIL import Image, ImageTk, ImageOps, ImageDraw
from .config import relative_to_assets


def _open_rgba(path: str):
    return Image.open(relative_to_assets(path)).convert("RGBA")


def _invert_rgba(image: Image.Image) -> Image.Image:
    """Invierte RGB conservando el canal alpha del PNG."""
    r, g, b, a = image.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageOps.invert(rgb)
    r, g, b = rgb.split()
    return Image.merge("RGBA", (r, g, b, a))


def load_image(path: str, size=None, invert=False):
    """Carga un PNG, opcionalmente lo redimensiona e invierte sus colores."""
    image = _open_rgba(path)
    if invert:
        image = _invert_rgba(image)
    if size is not None:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def make_line_style_icon(dashed=False, size=(42, 28), invert=False):
    """Icono compacto para alternar línea continua/punteada sin usar texto."""
    w, h = size
    bg = (255, 255, 255, 255)
    fg = (20, 20, 20, 255)
    image = Image.new("RGBA", size, bg)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1, 1, w-2, h-2), radius=5, outline=fg, width=2)
    y = h // 2
    if dashed:
        x = 7
        while x < w - 7:
            draw.line((x, y, min(x + 6, w - 7), y), fill=fg, width=3)
            x += 10
    else:
        draw.line((7, y, w - 7, y), fill=fg, width=3)
    if invert:
        image = _invert_rgba(image)
    return ImageTk.PhotoImage(image)
