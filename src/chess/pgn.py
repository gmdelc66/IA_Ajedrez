from tkinter import Button, Entry, Label, Toplevel, messagebox, filedialog
from src.common.config import canvas
from src.common.images import load_image
import chess.pgn
from .pattern import Pattern
from .pieces import chess_board_to_position


class PGN:
    """Lectura y navegación de partidas PGN."""

    def __init__(self, board_set_board, board_set_moves_text=None) -> None:
        self.board_set_board = board_set_board
        self.board_set_moves_text = board_set_moves_text or (lambda text: None)
        self.games = []
        self.games_num = 0
        self.game_moves = []
        self.moves = 0
        self.close = load_image("images/chess/close.png", (40, 40))
        self.info = load_image("images/chess/info.png", (40, 40))
        self.next_icon = load_image("images/chess/regresa.png", (38, 38))
        # Se crea el icono anterior invirtiendo horizontalmente en common.images no es necesario;
        # para mantener compatibilidad usamos un botón de texto únicamente en navegación secundaria.
        self.index_game = 0
        self.index = 0
        self.buttons = []
        self.label_num_games = None

    def _current_pgn_text(self):
        if not self.games:
            return ""
        game = self.games[self.index_game]
        headers = []
        for key, value in game.headers.items():
            if value:
                headers.append(f'[{key} "{value}"]')
        # SAN hasta la posición actualmente mostrada.
        board = game.board()
        san_tokens = []
        for ply, move in enumerate(self.game_moves[:self.index]):
            if board.turn:
                san_tokens.append(f"{board.fullmove_number}.")
            elif ply == 0:
                san_tokens.append(f"{board.fullmove_number}...")
            san_tokens.append(board.san(move))
            board.push(move)
        return "\n".join(headers) + "\n\n" + " ".join(san_tokens)

    def _sync_moves_text(self):
        self.board_set_moves_text(self._current_pgn_text())

    def get_next_game(self):
        if self.index_game + 1 < self.games_num:
            self.index_game += 1
            self.move_last(self.index_game)

    def get_back_game(self):
        if self.index_game - 1 >= 0:
            self.index_game -= 1
            self.move_last(self.index_game)

    def get_next(self):
        if self.index < len(self.game_moves):
            self.board.push(self.game_moves[self.index])
            self.index += 1
            self.board_set_board(self.parse(self.board))
            self._sync_moves_text()

    def get_back(self):
        if self.index > 0:
            self.index -= 1
            self.board.pop()
            self.board_set_board(self.parse(self.board))
            self._sync_moves_text()

    def read_file(self, is_pattern):
        """Abre un selector de archivo; conserva también una ventana manual por compatibilidad."""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo PGN" if not is_pattern else "Seleccionar archivo",
            filetypes=[("Archivos PGN", "*.pgn"), ("Todos los archivos", "*")]
        )
        if filename:
            self.get_games(filename, is_pattern)

    def move_last(self, i):
        game = self.games[i]
        self.game_moves = list(game.mainline_moves())
        self.board = game.board()
        for move in self.game_moves:
            self.board.push(move)
        self.moves = self.board.fullmove_number
        self.index = len(self.game_moves)
        self.board_set_board(self.parse(self.board))
        self._sync_moves_text()

    def get_games(self, name, is_pattern):
        try:
            self.games = []
            self.games_num = 0
            self.index_game = 0
            with open(name, encoding="utf-8", errors="replace") as pgn:
                while True:
                    game = chess.pgn.read_game(pgn)
                    if game is None:
                        break
                    self.games.append(game)
            self.games_num = len(self.games)
            if not self.games:
                messagebox.showwarning("PGN", "El archivo no contiene partidas PGN.")
                return

            if is_pattern:
                self.pattern = Pattern(self.games, self.board_set_board, self.parse)
                self.pattern.read_file()
            else:
                self.move_last(0)
                self.show_buttons()
        except (IOError, OSError) as exc:
            messagebox.showerror("Error", f"Archivo no encontrado o no legible.\n\n{exc}")

    @staticmethod
    def parse(board):
        """Convierte python-chess al formato interno canónico de piezas."""
        return chess_board_to_position(board)


    def clean(self):
        for button in self.buttons:
            try:
                button.destroy()
            except Exception:
                pass
        self.buttons = []
        if self.label_num_games is not None:
            try:
                self.label_num_games.destroy()
            except Exception:
                pass
            self.label_num_games = None
        self.board_set_moves_text("")

    def get_info(self):
        level = Toplevel(canvas)
        level.title("Información de la partida")
        level.geometry("420x350")
        i = 0
        for key in self.games[self.index_game].headers:
            txt = f"{key}: {self.games[self.index_game].headers[key]}"
            Label(level, text=txt, anchor="w").place(x=10, y=10 + i * 22)
            i += 1

    def show_buttons(self):
        self.clean()
        # Botones compactos de navegación. Los iconos nuevos se usan para cerrar/info.
        self.buttons = [
            Button(text='◀', command=self.get_back_game, width=3),
            Button(text='▶', command=self.get_next_game, width=3),
            Button(text='◀', command=self.get_back, width=3),
            Button(text='▶', command=self.get_next, width=3),
            Button(image=self.close, borderwidth=0, highlightthickness=0,
                   command=self.clean, relief="flat", bg="white"),
            Button(image=self.info, borderwidth=0, highlightthickness=0,
                   command=self.get_info, relief="flat", bg="white"),
        ]
        self.label_num_games = Label(text="Partidas: " + str(self.games_num), bg="white")
        self.label_num_games.place(x=80, y=35)
        self.buttons[0].place(x=185, y=30, width=38, height=32)
        self.buttons[1].place(x=227, y=30, width=38, height=32)
        self.buttons[2].place(x=270, y=30, width=38, height=32)
        self.buttons[3].place(x=312, y=30, width=38, height=32)
        self.buttons[5].place(x=500, y=28, width=40, height=40)
        self.buttons[4].place(x=545, y=28, width=40, height=40)
        self._sync_moves_text()
