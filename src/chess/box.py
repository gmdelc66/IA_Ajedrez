from src.common.config import canvas
from src.common.images import load_image
from .pieces import PIECE_SIZE_ADJUST

# Geometría de la imagen tablero_vacio_color.png en pantalla.
BOARD_IMAGE_X = 20
BOARD_IMAGE_Y = 80
BOARD_IMAGE_SIZE = 400
BOARD_SOURCE_SIZE = 1254
BOARD_SOURCE_MARGIN = 52
BOARD_SOURCE_INNER = 1144
BOARD_SQUARE = BOARD_IMAGE_SIZE * (BOARD_SOURCE_INNER / BOARD_SOURCE_SIZE) / 8
BOARD_LEFT = BOARD_IMAGE_X + BOARD_IMAGE_SIZE * (BOARD_SOURCE_MARGIN / BOARD_SOURCE_SIZE)
BOARD_TOP = BOARD_IMAGE_Y + BOARD_IMAGE_SIZE * (BOARD_SOURCE_MARGIN / BOARD_SOURCE_SIZE)
PIECE_SCREEN_SIZE = 44


class Box:
    """Representa una casilla y dibuja la pieza como PNG, no como carácter."""
    def __init__(self, row, col, back) -> None:
        self.canvas_box = None
        self.img_box = None
        self.row = row
        self.col = col
        self.x = BOARD_LEFT + BOARD_SQUARE * (col + 0.5)
        self.y = BOARD_TOP + BOARD_SQUARE * (row + 0.5)
        self.name = ""
        self.color = ""
        self.back = back


    def update_position(self, flipped=False):
        """Actualiza la posición visual sin cambiar la casilla lógica de la pieza."""
        row = 7 - self.row if flipped else self.row
        col = 7 - self.col if flipped else self.col
        self.x = BOARD_LEFT + BOARD_SQUARE * (col + 0.5)
        self.y = BOARD_TOP + BOARD_SQUARE * (row + 0.5)
        if self.canvas_box is not None:
            canvas.coords(self.canvas_box, self.x, self.y)

    def set_image(self):
        """Carga únicamente la pieza PNG. El tablero es una sola imagen de fondo."""
        self.img_box = None
        if self.get_name():
            name = self.get_name()
            factor = PIECE_SIZE_ADJUST.get(name, PIECE_SIZE_ADJUST.get(name[0], 1.0))
            size = max(1, int(round(PIECE_SCREEN_SIZE * factor)))
            self.img_box = load_image(
                "images/chess/pieces96/" + name + ".png",
                (size, size)
            )

    def show_on_screen(self):
        if self.img_box is not None:
            self.canvas_box = canvas.create_image(self.x, self.y, image=self.img_box)
        else:
            self.canvas_box = None

    def set_piece(self, name, color):
        self.name = name
        self.color = color
        self.clean()
        self.set_image()
        self.show_on_screen()

    def get_name(self) -> str:
        return self.name + self.color

    def clean(self):
        if self.canvas_box is not None:
            canvas.delete(self.canvas_box)
            self.canvas_box = None
