from ..cardHolder.interfaceCardH import InterfaceCardH
from src.common.config import canvas
from src.common.images import load_image
from .board import Board
from .pgn import PGN
from .menu import Menu
from src.common.interface import Interface, ToolTip
from tkinter import Text, Button


class InterfaceChess(Interface):
    """Interfaz principal del editor de diagramas de ajedrez."""

    def __init__(self, set_home) -> None:
        self.set_home = set_home
        self.board = Board()
        self.pgn = PGN(self.board.set_board, self.board.set_source_moves_text)
        self.pieces_menu = Menu(self.board)
        self.cards = InterfaceCardH(set_home, self.board, self.pieces_menu)
        self.play_history = [[], []]
        self.rec_history = None
        self.logo = 0
        self.logo_img = 0
        self.active_persistent_tool = None
        self.button_by_name = {}
        self.button_images_by_name = {}
        self.section_items = []

        button_info = [
            ("home", self.go_home),
            ("recrear_jugada", self.pieces_menu.set_menu),
            ("limpiar", self.board.set_empty_board),
            ("guardar_jugada", self.board.save),
            ("jugar", self.board.set_initial_board),
            ("buscar", lambda x=True: self.pgn.read_file(x)),
            ("ver", self.show_cards),
            ("guardar_historial", self.board.save_play_history),
            ("leer_PGN", lambda x=False: self.pgn.read_file(x)),
        ]
        super().__init__(button_info)

        self.icon_map = {
            "home": "home.png",
            "recrear_jugada": "seleccionar.png",
            "limpiar": "limpiar.png",
            "guardar_jugada": "guardar_imagen.png",
            "jugar": "caballo.png",
            "buscar": "buscar.png",
            "ver": "logo.png",
            "guardar_historial": "guardar_disco.png",
            "leer_PGN": "leer_PGN.png",
        }
        self.tooltips_text = {
            "home": "Volver al menú principal",
            "recrear_jugada": "Abrir herramientas de edición de piezas y flechas",
            "limpiar": "Limpiar completamente el tablero",
            "guardar_jugada": "Guardar imagen PNG y jugadas con el mismo nombre",
            "jugar": "Colocar la posición inicial de ajedrez",
            "buscar": "Buscar patrones o posiciones en un archivo",
            "ver": "Abrir el tarjetero de posiciones",
            "guardar_historial": "Guardar jugadas/posición en un archivo de texto",
            "leer_PGN": "Leer una partida desde un archivo PGN",
        }

    def click(self, event):
        if self.board.is_inside_board(event.x, event.y):
            if self.pieces_menu.get_is_arrow():
                self.board.set_arrow(
                    event,
                    color=self.pieces_menu.get_arrow_color(),
                    dashed=self.pieces_menu.get_arrow_dashed(),
                )
            elif self.pieces_menu.get_is_xmark():
                self.board.set_xmark(
                    event,
                    color=self.pieces_menu.get_arrow_color(),
                )
            else:
                idx = self.board.get_num(event.x, event.y)
                if self.pieces_menu.get_is_menu():
                    self.board.put_piece(idx)
                else:
                    self.board.move(idx)
        else:
            self.board.click_num = 0
            if self.pieces_menu.get_is_arrow():
                self.board.cancel_arrow_start()

    def show_cards(self):
        self.clean()
        self.delete_play_history()
        self.board.clean()
        self.cards.default_buttons()
        self.cards.show_cards()

    def go_home(self):
        self.clean()
        self.delete_play_history()
        self.board.clean()
        self.pieces_menu.clean()
        self.set_home()

    def delete_play_history(self):
        for side in self.play_history:
            if len(side) >= 3:
                try:
                    side[2].destroy()
                except Exception:
                    pass
        self.play_history = [[], []]

    def set_board(self):
        canvas.place(x=0, y=0)
        self.board.show_background()
        self.board.set_empty_board()

    def _set_toolbar_selected(self, name):
        """Invierte el icono seleccionado y restaura los demás."""
        for key, btn in self.button_by_name.items():
            normal, inverted = self.button_images_by_name[key]
            btn.configure(image=inverted if key == name else normal)

    def _run_toolbar_action(self, name, command, persistent=False):
        previous = self.active_persistent_tool
        self._set_toolbar_selected(name)
        if persistent:
            self.active_persistent_tool = name
        try:
            command()
        finally:
            if not persistent:
                # Las acciones de un solo paso destellan invertidas y luego vuelve
                # a mostrarse la herramienta persistente que estaba activa.
                btn = self.button_by_name.get(name)
                if btn is not None:
                    def restore():
                        target = self.active_persistent_tool or previous
                        if target in self.button_by_name:
                            self._set_toolbar_selected(target)
                        else:
                            self._set_toolbar_selected(None)
                    btn.after(220, restore)

    def create_buttons(self):
        """Barra lateral agrupada por función con hints y estado visual."""
        self.button_by_name = {}
        self.button_images_by_name = {}
        self.section_items = []

        command_map = dict(self.button_name)
        groups = [
            ("ARCHIVOS", ["guardar_jugada", "guardar_historial", "leer_PGN", "buscar"]),
            ("EDICIÓN", ["recrear_jugada", "limpiar", "jugar"]),
            ("BIBLIOTECA", ["ver"]),
            ("NAVEGACIÓN", ["home"]),
        ]
        # Dos columnas de 48 px en la zona derecha.
        base_x = 704
        col_gap = 58
        y = 56
        for group_name, names in groups:
            text_id = canvas.create_text(
                762, y, text=group_name, fill="#4C4C4C",
                font=("DejaVu Sans", 8, "bold")
            )
            self.section_items.append(text_id)
            y += 12
            for i, name in enumerate(names):
                row, col = divmod(i, 2)
                icon_name = self.icon_map[name]
                path = "images/chess/" + icon_name
                normal = load_image(path, (46, 46), invert=False)
                inverted = load_image(path, (46, 46), invert=True)
                self.img_buttons.extend([normal, inverted])
                persistent = (name == "recrear_jugada")
                btn = Button(
                    image=normal, borderwidth=0, highlightthickness=0,
                    relief="flat", bg="white", activebackground="white",
                    cursor="hand2"
                )
                btn.configure(command=lambda n=name, c=command_map[name], p=persistent:
                              self._run_toolbar_action(n, c, p))
                btn.place(
                    x=base_x + col * col_gap,
                    y=y + row * 52,
                    width=46, height=46
                )
                self.buttons.append(btn)
                self.button_by_name[name] = btn
                self.button_images_by_name[name] = (normal, inverted)
                self.tooltips.append(ToolTip(btn, self.tooltips_text[name]))
            rows = (len(names) + 1) // 2
            y += rows * 52 + 11

    def set_play_history(self):
        canvas.create_rectangle(432, 96, 603, 473, fill="#F2F2F2", outline="#C8C8C8")
        for i in range(2):
            self.play_history[i].append(None)
            self.play_history[i].append(None)
            self.play_history[i].append(Text(
                bd=0, bg="#F7F7F7", highlightthickness=1,
                highlightbackground="#D0D0D0", font=("DejaVu Sans", 9)
            ))
            self.play_history[i][2].place(
                x=440 + 81 * i, y=125, width=72, height=337
            )
        canvas.create_text(476, 110, text="Blancas", font=("DejaVu Sans", 9, "bold"))
        canvas.create_text(557, 110, text="Negras", font=("DejaVu Sans", 9, "bold"))

    def set_ornaments(self):
        self.logo_img = load_image("images/chess/logo.png", (52, 52))
        self.logo = canvas.create_image(733, 28, image=self.logo_img)

    def clean(self, all=True):
        self.button_by_name = {}
        self.button_images_by_name = {}
        self.active_persistent_tool = None
        self.section_items = []
        super().clean(all)
