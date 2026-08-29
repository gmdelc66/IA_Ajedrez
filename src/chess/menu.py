from src.common.config import canvas
from src.common.images import load_image, make_line_style_icon
from tkinter import Button, Frame, Label, Checkbutton, StringVar
from src.common.interface import Interface, ToolTip
from .pieces import PIECE_LABELS, PIECE_SIZE_ADJUST


class Menu(Interface):
    """Menú de edición: piezas, flechas configurables y borrado."""

    ARROW_COLORS = [
        ("Rojo", "#E53935"),
        ("Azul", "#1E88E5"),
        ("Verde", "#43A047"),
        ("Amarillo", "#FDD835"),
        ("Negro", "#202020"),
        ("Blanco", "#FFFFFF"),
        ("Naranja", "#FB8C00"),
        ("Morado", "#8E24AA"),
        ("Cian", "#00ACC1"),
        ("Magenta", "#D81B60"),
        ("Café", "#6D4C41"),
        ("Gris", "#757575"),
    ]

    def __init__(self, board) -> None:
        Interface.__init__(self, [])
        self.board = board
        self.pieces = ["R", "D", "T", "A", "C", "p"]
        self.is_select = True
        self.is_arrow = False
        self.is_xmark = False
        self.menu = False
        self.arrow_color = self.ARROW_COLORS[0][1]
        self.arrow_dashed = False
        self.selected_piece_button = None
        self.tool_buttons = {}
        self.tool_images = {}
        self.arrow_panel = None
        self.color_buttons = []
        self.line_style_button = None
        self.line_style_images = []
        self.turn_frame = None
        self.turn_var = StringVar(value="w")
        # El icono X se usa como herramienta de marca; "regresa" cierra edición.
        self.close_img = load_image("images/chess/regresa.png", (44, 44))

    def get_is_menu(self):
        return self.menu

    def get_is_arrow(self):
        return self.is_arrow

    def get_is_xmark(self):
        return self.is_xmark

    def get_arrow_color(self):
        return self.arrow_color

    def get_arrow_dashed(self):
        return self.arrow_dashed

    def add_arrow(self, _line):
        # Compatibilidad con llamadas antiguas: Board administra las flechas.
        pass

    def do_click(self, piece_id, button=None):
        if self.is_select:
            self.board.set_piece(piece_id)
            self._mark_piece_button(button)

    def _mark_piece_button(self, button):
        if self.selected_piece_button is not None:
            try:
                self.selected_piece_button.configure(relief="flat", bd=0)
            except Exception:
                pass
        self.selected_piece_button = button
        if button is not None:
            button.configure(relief="solid", bd=2)

    def set_pieces(self, y, color):
        start = len(self.img_buttons)
        for i in range(6):
            name = self.pieces[i] + color
            factor = PIECE_SIZE_ADJUST.get(name, PIECE_SIZE_ADJUST.get(name[0], 1.0))
            size = max(1, int(round(48 * factor)))
            image = load_image("images/chess/pieces96/" + name + ".png", (size, size))
            self.img_buttons.append(image)
            btn = Button(
                image=image, borderwidth=0, highlightthickness=0,
                relief="flat", bg="white", activebackground="white",
                cursor="hand2"
            )
            btn.configure(command=lambda x=name, b=btn: self.do_click(x, b))
            self.buttons.append(btn)
            btn.place(x=72.0 + (50 * i), y=y, width=48.0, height=48.0)
            ToolTip(btn, f"Colocar {self._piece_label(name)}")

    @staticmethod
    def _piece_label(name):
        side = "negro" if name.endswith("N") else "blanco"
        return f"{PIECE_LABELS.get(name[0], 'pieza')} {side}"

    def _load_tool_images(self, name):
        path_map = {
            "arrow": "flecha.png",
            "xmark": "close.png",
            "select": "seleccionar.png",
            "delete": "borrar.png",
            "fen": "guardar_en_disco.png",
            "rotate": "rotar.png",
        }
        path = "images/chess/" + path_map[name]
        return (
            load_image(path, (44, 44), invert=False),
            load_image(path, (44, 44), invert=True),
        )

    def _update_tool_visuals(self):
        if self.is_arrow:
            active = "arrow"
        elif self.is_xmark:
            active = "xmark"
        else:
            active = "select"
        for name, btn in self.tool_buttons.items():
            normal, inverted = self.tool_images[name]
            btn.configure(image=inverted if name == active else normal)

    def switch_var(self, val):
        # 0 = flecha, 1 = selección/mover piezas, 2 = marcar X
        if val == 0:
            self.is_arrow = True
            self.is_xmark = False
            self.is_select = False
            self.board.set_piece("")
            self._mark_piece_button(None)
            self.show_arrow_panel(show_line_style=True)
        elif val == 2:
            self.is_arrow = False
            self.is_xmark = True
            self.is_select = False
            self.board.cancel_arrow_start()
            self.board.set_piece("")
            self._mark_piece_button(None)
            self.show_arrow_panel(show_line_style=False)
        else:
            self.is_select = True
            self.is_arrow = False
            self.is_xmark = False
            self.board.cancel_arrow_start()
            self.hide_arrow_panel()
        self._update_tool_visuals()

    def _flash_tool(self, name, action):
        btn = self.tool_buttons.get(name)
        normal, inverted = self.tool_images.get(name, (None, None))
        if btn is not None and inverted is not None:
            btn.configure(image=inverted)
            btn.update_idletasks()
        try:
            return action()
        finally:
            if btn is not None and normal is not None:
                btn.after(180, lambda: btn.winfo_exists() and self._update_tool_visuals())

    def _open_fen(self):
        if self.board.open_fen_dialog():
            self.turn_var.set(self.board.side_to_move)

    def _rotate_board(self):
        self.board.rotate_board()

    def _set_turn(self):
        self.board.set_side_to_move(self.turn_var.get())

    def _show_turn_selector(self):
        if self.turn_frame is not None:
            try:
                self.turn_frame.destroy()
            except Exception:
                pass
        self.turn_var.set(self.board.side_to_move)
        self.turn_frame = Frame(canvas, bg="#F6F6F6", bd=1, relief="solid")
        self.turn_frame.place(x=432, y=563, width=170, height=48)
        Label(self.turn_frame, text="Turno", bg="#F6F6F6", fg="#111111",
              font=("DejaVu Sans", 8, "bold")).place(x=6, y=2)
        # Un solo selector: ON = juegan blancas; OFF = juegan negras.
        Checkbutton(
            self.turn_frame, text="Blancas", variable=self.turn_var,
            onvalue="w", offvalue="b", command=self._set_turn,
            bg="#F6F6F6", fg="#111111", activebackground="#F6F6F6",
            activeforeground="#111111", selectcolor="#FFFFFF",
            highlightthickness=0, bd=0, font=("DejaVu Sans", 8, "bold")
        ).place(x=4, y=19)
        Label(self.turn_frame, text="OFF = Negras", bg="#F6F6F6", fg="#333333",
              font=("DejaVu Sans", 7)).place(x=82, y=21)

    def delete(self):
        if self.is_arrow or self.is_xmark:
            self.board.delete_last_annotation()
        else:
            self.board.set_piece("")
            self._mark_piece_button(None)
        self._flash_delete()

    def _flash_delete(self):
        btn = self.tool_buttons.get("delete")
        if btn is None:
            return
        normal, inverted = self.tool_images["delete"]
        btn.configure(image=inverted)
        btn.after(180, lambda: btn.winfo_exists() and btn.configure(image=normal))

    def _select_color(self, color):
        self.arrow_color = color
        self._refresh_color_selection()
        # Si ya se había elegido origen, actualiza el resaltado con el nuevo color.
        if self.board.arrow_start_index is not None:
            idx = self.board.arrow_start_index
            self.board.cancel_arrow_start()
            self.board.arrow_start_index = idx
            x0, y0, x1, y1 = self.board._square_bounds(idx)
            self.board.arrow_highlight_id = canvas.create_rectangle(
                x0, y0, x1, y1, fill=color, outline=color, width=2
            )
            self.board._raise_pieces()

    def _refresh_color_selection(self):
        for btn, color in self.color_buttons:
            if color == self.arrow_color:
                btn.configure(relief="solid", bd=3, highlightthickness=1, highlightbackground="#111111")
            else:
                btn.configure(relief="flat", bd=1, highlightthickness=0)

    def _toggle_line_style(self):
        self.arrow_dashed = not self.arrow_dashed
        self._refresh_line_style_icon()

    def _refresh_line_style_icon(self):
        if self.line_style_button is None:
            return
        # Índice 0 continua, 1 punteada.
        self.line_style_button.configure(image=self.line_style_images[1 if self.arrow_dashed else 0])
        ToolTip(self.line_style_button, "Línea punteada" if self.arrow_dashed else "Línea continua")

    def show_arrow_panel(self, show_line_style=True):
        """Muestra las opciones de color debajo del panel de jugadas.

        La zona de jugadas termina aproximadamente en y=473; por eso este
        panel es compacto y comienza debajo, evitando cubrir el historial.
        """
        self.hide_arrow_panel()
        self.arrow_panel = Frame(canvas, bg="#F6F6F6", bd=1, relief="solid")
        self.arrow_panel.place(x=432, y=477, width=170, height=82)
        Label(self.arrow_panel, text="Color", bg="#F6F6F6", fg="#111111",
              font=("DejaVu Sans", 8, "bold")).place(x=6, y=2)

        self.color_buttons = []
        for i, (name, color) in enumerate(self.ARROW_COLORS):
            btn = Button(
                self.arrow_panel, bg=color, activebackground=color,
                command=lambda c=color: self._select_color(c),
                cursor="hand2"
            )
            row, col = divmod(i, 6)
            btn.place(x=7 + col * 25, y=18 + row * 20, width=20, height=17)
            self.color_buttons.append((btn, color))
            ToolTip(btn, name)
        self._refresh_color_selection()

        if show_line_style:
            self.line_style_images = [
                make_line_style_icon(False, (38, 22)),
                make_line_style_icon(True, (38, 22)),
            ]
            self.line_style_button = Button(
                self.arrow_panel, image=self.line_style_images[1 if self.arrow_dashed else 0],
                borderwidth=0, highlightthickness=0, relief="flat",
                command=self._toggle_line_style, bg="#F6F6F6", activebackground="#E6E6E6",
                cursor="hand2"
            )
            self.line_style_button.place(x=7, y=56, width=38, height=22)
            Label(self.arrow_panel, text="Continua / punteada", bg="#F6F6F6", fg="#111111",
                  font=("DejaVu Sans", 8)).place(x=52, y=58)
            ToolTip(self.line_style_button, "Cambiar estilo de línea")
        else:
            Label(self.arrow_panel, text="Marca X", bg="#F6F6F6", fg="#111111",
                  font=("DejaVu Sans", 8)).place(x=7, y=58)

    def hide_arrow_panel(self):
        if self.arrow_panel is not None:
            try:
                self.arrow_panel.destroy()
            except Exception:
                pass
        self.arrow_panel = None
        self.color_buttons = []
        self.line_style_button = None
        self.line_style_images = []
        # El selector de turno es independiente del panel de flechas.

    def set_menu(self):
        if self.menu:
            return
        self.menu = True
        self.set_pieces(25.0, "N")
        self.set_pieces(486.0, "B")

        tips = {
            "arrow": "Dibujar flechas y elegir color/estilo",
            "xmark": "Marcar una X del color seleccionado",
            "select": "Seleccionar, mover o colocar piezas",
            "fen": "Pegar o leer archivo FEN",
            "rotate": "Rotar tablero: cambiar vista blancas/negras",
            "delete": "Borrar pieza seleccionada o la última anotación",
        }
        commands = {
            "arrow": lambda: self.switch_var(0),
            "xmark": lambda: self.switch_var(2),
            "select": lambda: self.switch_var(1),
            "fen": lambda: self._flash_tool("fen", self._open_fen),
            "rotate": lambda: self._flash_tool("rotate", self._rotate_board),
            "delete": self.delete,
        }
        for i, name in enumerate(("arrow", "xmark", "select", "fen", "rotate", "delete")):
            self.tool_images[name] = self._load_tool_images(name)
            normal, inverted = self.tool_images[name]
            btn = Button(
                image=normal, borderwidth=0, highlightthickness=0,
                command=commands[name], relief="flat", bg="white",
                activebackground="white", cursor="hand2"
            )
            self.buttons.append(btn)
            self.tool_buttons[name] = btn
            btn.place(x=390.0 + i * 47, y=27.0, width=44.0, height=44.0)
            ToolTip(btn, tips[name])

        close_btn = Button(
            image=self.close_img, borderwidth=0, highlightthickness=0,
            command=self.clean, relief="flat", bg="white",
            activebackground="white", cursor="hand2"
        )
        self.buttons.append(close_btn)
        close_btn.place(x=672.0, y=27.0, width=44.0, height=44.0)
        ToolTip(close_btn, "Cerrar herramientas de edición")
        self._update_tool_visuals()
        self._show_turn_selector()

    def clean(self):
        self.hide_arrow_panel()
        if self.turn_frame is not None:
            try:
                self.turn_frame.destroy()
            except Exception:
                pass
            self.turn_frame = None
        self.board.cancel_arrow_start()
        super().clean(False)
        self.is_select = True
        self.is_arrow = False
        self.is_xmark = False
        self.menu = False
        self.board.set_piece("")
        self.selected_piece_button = None
        self.tool_buttons = {}
        self.tool_images = {}
