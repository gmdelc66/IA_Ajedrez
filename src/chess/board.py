from pathlib import Path
from tkinter.constants import LAST
from .box import (
    Box, BOARD_IMAGE_X, BOARD_IMAGE_Y, BOARD_IMAGE_SIZE,
    BOARD_SOURCE_MARGIN, BOARD_SOURCE_INNER, BOARD_SOURCE_SIZE,
    BOARD_LEFT, BOARD_TOP, BOARD_SQUARE
)
from tkinter import messagebox, Frame, filedialog, Toplevel, Label, Text, Button, END
from src.common.config import canvas, relative_to_assets, window
from src.common.images import load_image
from .pieces import (
    PIECE_SIZE_ADJUST,
    PIECE_TO_FEN,
    chess_board_to_position,
    normalize_piece_id,
    normalize_position,
    serialize_position,
)
from PIL import Image, ImageDraw, ImageTk
import chess


class Board:
    """Editor de posiciones usando tablero e imágenes PNG."""

    def __init__(self) -> None:
        self.board = []
        self.frame = Frame(canvas)
        self.frame.place()

        self.click_num = 0
        self.x1 = self.x2 = self.y1 = self.y2 = 0
        self.id_num = 0
        self.id1 = self.id2 = 0
        self.piece = ""

        self.board_background_img = None
        self.board_background_id = None
        self.move_history = []
        self.source_moves_text = ""

        # Anotaciones gráficas (flechas) y selección temporal de casilla.
        self.arrow_annotations = []
        self.xmark_annotations = []
        # Historial único para borrar anotaciones en el orden real en que se crearon.
        self.annotation_history = []
        self.arrow_start_index = None
        self.arrow_highlight_id = None
        self.flipped = False
        self.side_to_move = "w"
        self.fen_castling = "-"
        self.fen_ep = "-"
        self.fen_halfmove = 0
        self.fen_fullmove = 1

    def _board_background_pil(self):
        """Devuelve el tablero orientado para blancas o negras con coordenadas legibles."""
        path = relative_to_assets("images/chess/tablero_vacio_color.png")
        image = Image.open(path).convert("RGBA")
        if not self.flipped:
            return image

        # Rotar todo invierte correctamente el orden de coordenadas (h..a / 1..8),
        # pero deja las letras y números boca abajo. Se corrige cada etiqueta
        # individualmente manteniendo su nueva posición.
        image = image.rotate(180)
        sq = BOARD_SOURCE_INNER / 8.0
        m = BOARD_SOURCE_MARGIN
        size = BOARD_SOURCE_SIZE

        # Etiquetas superiores e inferiores.
        for col in range(8):
            cx = m + sq * (col + 0.5)
            x0 = max(0, int(cx - sq * 0.42))
            x1 = min(size, int(cx + sq * 0.42))
            for y0, y1 in ((0, int(m)), (int(size-m), size)):
                crop = image.crop((x0, y0, x1, y1)).rotate(180)
                image.paste(crop, (x0, y0))

        # Etiquetas laterales.
        for row in range(8):
            cy = m + sq * (row + 0.5)
            y0 = max(0, int(cy - sq * 0.42))
            y1 = min(size, int(cy + sq * 0.42))
            for x0, x1 in ((0, int(m)), (int(size-m), size)):
                crop = image.crop((x0, y0, x1, y1)).rotate(180)
                image.paste(crop, (x0, y0))
        return image

    def show_background(self):
        """Dibuja el tablero completo con la orientación actual."""
        if self.board_background_id is not None:
            canvas.delete(self.board_background_id)
        image = self._board_background_pil().resize(
            (BOARD_IMAGE_SIZE, BOARD_IMAGE_SIZE), Image.Resampling.LANCZOS
        )
        self.board_background_img = ImageTk.PhotoImage(image)
        self.board_background_id = canvas.create_image(
            BOARD_IMAGE_X, BOARD_IMAGE_Y, anchor="nw", image=self.board_background_img
        )
        canvas.tag_lower(self.board_background_id)

    def is_inside_board(self, x, y):
        return (BOARD_LEFT <= x < BOARD_LEFT + BOARD_SQUARE * 8 and
                BOARD_TOP <= y < BOARD_TOP + BOARD_SQUARE * 8)

    def get_num(self, x, y):
        col = int((x - BOARD_LEFT) // BOARD_SQUARE)
        row = int((y - BOARD_TOP) // BOARD_SQUARE)
        col = max(0, min(7, col))
        row = max(0, min(7, row))
        if self.flipped:
            row, col = 7 - row, 7 - col
        return 8 * row + col

    @staticmethod
    def _square_name(index):
        row, col = divmod(index, 8)
        return f"{'abcdefgh'[col]}{8-row}"

    def move(self, id):
        """Mueve una pieza usando directamente sus imágenes PNG."""
        if self.id_num == 0:
            self.id1 = id
            self.id_num = 1
            return

        self.id2 = id
        self.id_num = 0
        name = self.board[self.id1].get_name()
        if name and not self.board[self.id2].get_name():
            origin = self._square_name(self.id1)
            target = self._square_name(self.id2)
            self.board[self.id1].set_piece("", "")
            self.board[self.id2].set_piece(name[0], name[1])
            self.move_history.append(f"{origin}-{target}")
            self._raise_xmarks()

    def _display_row_col(self, index):
        row, col = divmod(index, 8)
        if self.flipped:
            row, col = 7 - row, 7 - col
        return row, col

    def _square_center(self, index):
        row, col = self._display_row_col(index)
        return (
            BOARD_LEFT + BOARD_SQUARE * (col + 0.5),
            BOARD_TOP + BOARD_SQUARE * (row + 0.5),
        )

    def _square_bounds(self, index):
        row, col = self._display_row_col(index)
        x0 = BOARD_LEFT + BOARD_SQUARE * col
        y0 = BOARD_TOP + BOARD_SQUARE * row
        return x0, y0, x0 + BOARD_SQUARE, y0 + BOARD_SQUARE

    def _raise_xmarks(self):
        for ann in self.xmark_annotations:
            for cid in ann.get("canvas_ids", ()):
                try:
                    canvas.tag_raise(cid)
                except Exception:
                    pass

    def _refresh_annotation_geometry(self):
        """Reposiciona flechas y X después de rotar el tablero."""
        for ann in self.arrow_annotations:
            x1, y1 = self._square_center(ann["start"])
            x2, y2 = self._square_center(ann["end"])
            canvas.coords(ann["canvas_id"], x1, y1, x2, y2)
        for ann in self.xmark_annotations:
            x0, y0, x1, y1 = self._square_bounds(ann["index"])
            margin = BOARD_SQUARE * 0.22
            ids = ann.get("canvas_ids", ())
            if len(ids) == 2:
                canvas.coords(ids[0], x0+margin, y0+margin, x1-margin, y1-margin)
                canvas.coords(ids[1], x0+margin, y1-margin, x1-margin, y0+margin)
        self._raise_pieces()
        self._raise_xmarks()

    def rotate_board(self):
        """Gira visualmente el tablero 180° sin alterar la posición lógica/FEN."""
        self.cancel_arrow_start()
        self.flipped = not self.flipped
        self.show_background()
        for box in self.board:
            box.update_position(self.flipped)
        self._refresh_annotation_geometry()

    def set_side_to_move(self, side):
        self.side_to_move = "b" if str(side).lower().startswith("b") or str(side).lower().startswith("n") else "w"


    def _raise_pieces(self):
        for box in self.board:
            if box.canvas_box is not None:
                canvas.tag_raise(box.canvas_box)

    def cancel_arrow_start(self):
        """Cancela el primer punto de una flecha y restaura visualmente la casilla."""
        if self.arrow_highlight_id is not None:
            canvas.delete(self.arrow_highlight_id)
            self.arrow_highlight_id = None
        self.arrow_start_index = None
        self.click_num = 0

    def set_arrow(self, event, color="#E53935", dashed=False):
        """
        Flecha en dos clics:
        1) resalta la casilla inicial con el color seleccionado;
        2) restaura esa casilla y traza del centro exacto de origen al centro
           exacto del destino, a cualquier ángulo.
        """
        index = self.get_num(event.x, event.y)
        if self.arrow_start_index is None:
            self.arrow_start_index = index
            x0, y0, x1, y1 = self._square_bounds(index)
            if self.arrow_highlight_id is not None:
                canvas.delete(self.arrow_highlight_id)
            self.arrow_highlight_id = canvas.create_rectangle(
                x0, y0, x1, y1, fill=color, outline=color, width=2
            )
            # La pieza y cualquier X quedan visibles sobre el resaltado temporal.
            self._raise_pieces()
            self._raise_xmarks()
            self.click_num = 1
            return None

        start_index = self.arrow_start_index
        end_index = index
        self.cancel_arrow_start()
        if start_index == end_index:
            return None

        x1, y1 = self._square_center(start_index)
        x2, y2 = self._square_center(end_index)
        dash = (10, 7) if dashed else None
        line = canvas.create_line(
            x1, y1, x2, y2, fill=color, width=5,
            arrow=LAST, arrowshape=(14, 18, 7), dash=dash,
            capstyle="round", joinstyle="round"
        )
        # Las flechas siempre quedan debajo de las piezas y de las marcas X.
        self._raise_pieces()
        self._raise_xmarks()
        ann = {
            "canvas_id": line,
            "start": start_index,
            "end": end_index,
            "color": color,
            "dashed": bool(dashed),
        }
        self.arrow_annotations.append(ann)
        self.annotation_history.append(("arrow", ann))
        return line


    def set_xmark(self, event, color="#E53935"):
        """Dibuja una X centrada en la casilla seleccionada con el color activo."""
        index = self.get_num(event.x, event.y)
        x0, y0, x1, y1 = self._square_bounds(index)
        margin = BOARD_SQUARE * 0.22
        width = max(3, int(BOARD_SQUARE * 0.10))
        l1 = canvas.create_line(
            x0 + margin, y0 + margin, x1 - margin, y1 - margin,
            fill=color, width=width, capstyle="round"
        )
        l2 = canvas.create_line(
            x0 + margin, y1 - margin, x1 - margin, y0 + margin,
            fill=color, width=width, capstyle="round"
        )
        self._raise_pieces()
        canvas.tag_raise(l1)
        canvas.tag_raise(l2)
        ann = {
            "canvas_ids": (l1, l2),
            "index": index,
            "color": color,
        }
        self.xmark_annotations.append(ann)
        self.annotation_history.append(("xmark", ann))
        return (l1, l2)

    def delete_last_annotation(self):
        """Borra la última anotación creada, sea flecha o X, sin importar la herramienta activa."""
        self.cancel_arrow_start()
        while self.annotation_history:
            kind, ann = self.annotation_history.pop()
            if kind == "arrow":
                if ann in self.arrow_annotations:
                    self.arrow_annotations.remove(ann)
                try:
                    canvas.delete(ann.get("canvas_id"))
                except Exception:
                    pass
                return
            if kind == "xmark":
                if ann in self.xmark_annotations:
                    self.xmark_annotations.remove(ann)
                for cid in ann.get("canvas_ids", ()):
                    try:
                        canvas.delete(cid)
                    except Exception:
                        pass
                return

    def delete_last_xmark(self):
        if not self.xmark_annotations:
            return
        ann = self.xmark_annotations.pop()
        self.annotation_history = [h for h in self.annotation_history if h[1] is not ann]
        for cid in ann.get("canvas_ids", ()):
            try:
                canvas.delete(cid)
            except Exception:
                pass

    def delete_last_arrow(self):
        self.cancel_arrow_start()
        if not self.arrow_annotations:
            return
        ann = self.arrow_annotations.pop()
        self.annotation_history = [h for h in self.annotation_history if h[1] is not ann]
        try:
            canvas.delete(ann["canvas_id"])
        except Exception:
            pass

    def clear_annotations(self):
        self.cancel_arrow_start()
        for ann in self.arrow_annotations:
            try:
                canvas.delete(ann["canvas_id"])
            except Exception:
                pass
        for ann in self.xmark_annotations:
            for cid in ann.get("canvas_ids", ()):
                try:
                    canvas.delete(cid)
                except Exception:
                    pass
        self.arrow_annotations = []
        self.xmark_annotations = []
        self.annotation_history = []

    def set_piece(self, piece):
        self.piece = piece

    def put_piece(self, id):
        if self.piece:
            self.board[id].set_piece(self.piece[0], self.piece[1])
        else:
            self.board[id].set_piece("", "")
        self._raise_xmarks()

    # Las coordenadas ya están integradas en tablero_vacio_color.png.
    def set_board_num(self):
        pass

    def set_board_letters(self):
        pass

    def set_empty_board(self, clear_history=True):
        """Muestra el nuevo tablero vacío y conserva una sola imagen de fondo."""
        if self.board_background_id is None:
            self.show_background()
        num = 0
        for row in range(8):
            for col in range(8):
                idx = 8 * row + col
                if len(self.board) < 64:
                    box = Box(row, col, int(num))
                    self.board.append(box)
                    box.update_position(self.flipped)
                else:
                    self.board[idx].set_piece("", "")
                    self.board[idx].update_position(self.flipped)
                num = not num
            num = not num
        if clear_history:
            self.move_history = []
            self.source_moves_text = ""
            self.side_to_move = "w"
            self.fen_castling = "-"
            self.fen_ep = "-"
            self.fen_halfmove = 0
            self.fen_fullmove = 1
            self.clear_annotations()

        # Anotaciones gráficas (flechas) y selección temporal de casilla.
        self.arrow_annotations = []
        self.xmark_annotations = []
        # Historial único para borrar anotaciones en el orden real en que se crearon.
        self.annotation_history = []
        self.arrow_start_index = None
        self.arrow_highlight_id = None
        self.id_num = 0

    def set_board(self, pieces):
        """Muestra una posición usando el formato interno canónico de 64 casillas.

        Por compatibilidad, ``normalize_position`` también acepta registros
        antiguos del tarjetero (por ejemplo ``RB0``/``RB1``). A partir de ese
        punto todo el programa trabaja únicamente con ``RB``, ``DN``, etc.
        """
        if self.board_background_id is None:
            self.show_background()
        if len(self.board) < 64:
            self.set_empty_board(clear_history=False)

        try:
            position = normalize_position(pieces)
        except ValueError as exc:
            messagebox.showerror("Posición no válida", str(exc))
            return False

        for idx, piece_id in enumerate(position):
            if piece_id:
                self.board[idx].set_piece(piece_id[0], piece_id[1])
            else:
                self.board[idx].set_piece("", "")
            self.board[idx].update_position(self.flipped)

        self._raise_xmarks()
        return True

    def get_position(self):
        """Devuelve las 64 casillas en el formato interno canónico."""
        return [box.get_name() for box in self.board]

    def get_coord(self):
        """Serializa la posición para el tarjetero sin mezclar pieza y casilla."""
        return serialize_position(self.get_position())


    def to_string(self) -> str:
        """Genera el tablero con la fuente histórica usada por el PDF del tarjetero.

        Esta conversión es sólo de presentación: internamente las piezas siguen
        usando siempre su identificador canónico de dos caracteres.
        """
        empty_glyph = {0: "", 1: ""}
        piece_glyph = {
            ("RB", 0): "", ("DB", 0): "", ("TB", 0): "",
            ("AB", 0): "", ("CB", 0): "", ("pB", 0): "",
            ("RB", 1): "", ("DB", 1): "", ("TB", 1): "",
            ("AB", 1): "", ("CB", 1): "", ("pB", 1): "",
            ("RN", 0): "", ("DN", 0): "", ("TN", 0): "",
            ("AN", 0): "", ("CN", 0): "", ("pN", 0): "",
            ("RN", 1): "", ("DN", 1): "", ("TN", 1): "",
            ("AN", 1): "", ("CN", 1): "", ("pN", 1): "",
        }
        out = " <br />"
        for row in range(8):
            out += ""
            for col in range(8):
                box = self.board[8 * row + col]
                piece_id = box.get_name()
                out += piece_glyph[(piece_id, box.back)] if piece_id else empty_glyph[box.back]
            out += " <br />"
        out += "<br />"
        return out


    def set_source_moves_text(self, text):
        self.source_moves_text = text or ""

    def to_fen(self):
        rows = []
        for row in range(8):
            empty = 0
            out = ""
            for col in range(8):
                name = self.board[8 * row + col].get_name()
                if not name:
                    empty += 1
                else:
                    if empty:
                        out += str(empty)
                        empty = 0
                    out += PIECE_TO_FEN[name]
            if empty:
                out += str(empty)
            rows.append(out)
        return f"{'/'.join(rows)} {self.side_to_move} {self.fen_castling} {self.fen_ep} {self.fen_halfmove} {self.fen_fullmove}"

    @staticmethod
    def _extract_fen_from_text(text):
        """Extrae un FEN puro desde texto plano o desde nuestros TXT guardados."""
        raw = (text or "").replace("\ufeff", "").strip()
        if not raw:
            raise ValueError("El campo FEN está vacío.")

        # 1) Formato generado por este programa:
        #    Posición (FEN):
        #    <fen>
        lines = [line.strip() for line in raw.splitlines()]
        for i, line in enumerate(lines):
            if line.lower().startswith("posición (fen)") or line.lower().startswith("posicion (fen)"):
                for candidate in lines[i + 1:]:
                    if candidate:
                        return candidate

        # 2) Un FEN puro pegado directamente.
        compact = " ".join(raw.split())
        parts = compact.split()
        if len(parts) in (1, 6) and "/" in parts[0]:
            return compact

        # 3) Buscar una línea que tenga aspecto de FEN dentro de cualquier TXT.
        for line in lines:
            candidate = " ".join(line.split())
            parts = candidate.split()
            if len(parts) in (1, 6) and parts and "/" in parts[0]:
                return candidate

        raise ValueError("No se encontró una posición FEN reconocible en el texto o archivo seleccionado.")

    @classmethod
    def _normalize_fen_text(cls, text):
        fen = cls._extract_fen_from_text(text)
        fen = " ".join(fen.strip().split())
        parts = fen.split()
        if len(parts) == 1:
            fen += " w - - 0 1"
        elif len(parts) != 6:
            raise ValueError("Un FEN debe contener 6 campos: posición, turno, enroque, al paso, medio movimiento y número de jugada.")
        return fen

    def load_fen(self, text):
        """Valida un FEN y carga la posición. Devuelve (ok, mensaje)."""
        try:
            fen = self._normalize_fen_text(text)
            chess_board = chess.Board(fen)
        except ValueError as exc:
            msg = str(exc)
            translations = {
                "invalid character in position part of fen": "La posición contiene un carácter de pieza no válido.",
                "expected 8 rows in position part of fen": "La posición debe contener exactamente 8 filas separadas por '/'.",
                "expected 8 columns per row in position part of fen": "Cada fila del tablero debe sumar exactamente 8 casillas.",
                "expected 'w' or 'b' for turn part of fen": "El turno debe ser 'w' (blancas) o 'b' (negras).",
            }
            for key, value in translations.items():
                if key in msg.lower():
                    msg = value
                    break
            return False, msg
        except Exception as exc:
            return False, str(exc)

        pieces = chess_board_to_position(chess_board)

        self.clear_annotations()
        self.move_history = []
        self.source_moves_text = ""
        self.set_board(pieces)
        self.side_to_move = "w" if chess_board.turn == chess.WHITE else "b"
        parts = fen.split()
        self.fen_castling = parts[2]
        self.fen_ep = parts[3]
        self.fen_halfmove = int(parts[4])
        self.fen_fullmove = int(parts[5])
        return True, ""

    def open_fen_dialog(self):
        """Permite pegar/editar un FEN o leerlo desde un archivo."""
        dialog = Toplevel(window)
        dialog.title("Pegar o leer archivo FEN")
        dialog.configure(bg="#FFFFFF")
        dialog.transient(window)
        dialog.resizable(True, False)
        dialog.grab_set()

        Label(dialog, text="Posición FEN", bg="#FFFFFF", fg="#111111",
              font=("DejaVu Sans", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        editor = Text(dialog, height=4, width=78, wrap="word", font=("DejaVu Sans Mono", 9))
        editor.pack(fill="x", padx=14, pady=(0, 10))
        editor.insert("1.0", self.to_fen())
        result = {"ok": False}

        buttons = Frame(dialog, bg="#FFFFFF")
        buttons.pack(fill="x", padx=14, pady=(0, 12))

        def read_file():
            filename = filedialog.askopenfilename(
                parent=dialog, title="Leer archivo FEN",
                # Mostrar todos los archivos por defecto; .fen y .txt quedan como filtros opcionales.
                filetypes=[("Todos los archivos", "*.*"), ("Archivos FEN", "*.fen"), ("Archivos de texto", "*.txt")]
            )
            if not filename:
                return
            try:
                text = Path(filename).read_text(encoding="utf-8").strip()
            except UnicodeDecodeError:
                text = Path(filename).read_text(encoding="latin-1").strip()
            except Exception as exc:
                messagebox.showerror("No se pudo leer el archivo", str(exc), parent=dialog)
                return
            try:
                fen_text = self._extract_fen_from_text(text)
            except ValueError as exc:
                messagebox.showerror("FEN no encontrado", str(exc), parent=dialog)
                return
            editor.delete("1.0", END)
            # El editor muestra únicamente el FEN, aunque el archivo sea uno de nuestros TXT
            # con encabezados, jugadas u otras notas. Así puede editarse/copiarse directamente.
            editor.insert("1.0", fen_text)

        def accept():
            ok, error = self.load_fen(editor.get("1.0", END))
            if not ok:
                messagebox.showerror("FEN no válido", error, parent=dialog)
                editor.focus_set()
                return
            result["ok"] = True
            dialog.destroy()

        Button(buttons, text="Leer archivo…", command=read_file, width=16).pack(side="left")
        Button(buttons, text="Cancelar", command=dialog.destroy, width=12).pack(side="right", padx=(8, 0))
        Button(buttons, text="Aceptar", command=accept, width=12).pack(side="right")

        dialog.update_idletasks()
        x = window.winfo_rootx() + max(0, (window.winfo_width() - dialog.winfo_reqwidth()) // 2)
        y = window.winfo_rooty() + max(0, (window.winfo_height() - dialog.winfo_reqheight()) // 2)
        dialog.geometry(f"+{x}+{y}")
        editor.focus_set()
        window.wait_window(dialog)
        return result["ok"]

    def _moves_text(self):
        lines = ["Posición (FEN):", self.to_fen(), "", f"Juegan: {'Blancas' if self.side_to_move == 'w' else 'Negras'}", ""]
        if self.source_moves_text.strip():
            lines.extend(["Jugadas / PGN cargado:", self.source_moves_text.strip(), ""])
        if self.move_history:
            lines.append("Movimientos realizados manualmente en el editor:")
            for i, move in enumerate(self.move_history, 1):
                lines.append(f"{i}. {move}")
        if not self.source_moves_text.strip() and not self.move_history:
            lines.append("No hay jugadas registradas; se guardó únicamente la posición actual.")
        return "\n".join(lines).rstrip() + "\n"


    def _show_saving_dialog(self, paths):
        """Ventana temporal sin botones mientras se escribe el archivo."""
        dialog = Toplevel(window)
        dialog.title("Guardando")
        dialog.configure(bg="#FFFFFF")
        dialog.resizable(False, False)
        dialog.transient(window)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        if isinstance(paths, (str, Path)):
            paths = [paths]
        path_text = "\n".join(str(Path(p)) for p in paths)

        Label(
            dialog, text="Guardando archivo…", bg="#FFFFFF", fg="#111111",
            font=("DejaVu Sans", 11, "bold")
        ).pack(padx=24, pady=(18, 8))
        Label(
            dialog, text=path_text, bg="#FFFFFF", fg="#222222", justify="left",
            wraplength=520, font=("DejaVu Sans", 9)
        ).pack(padx=24, pady=(0, 18))

        # Centra la ventana sobre el editor y obliga a dibujarla antes de iniciar
        # la operación de guardado. Se destruye automáticamente al terminar.
        dialog.update_idletasks()
        width = max(430, dialog.winfo_reqwidth())
        height = dialog.winfo_reqheight()
        x = window.winfo_rootx() + max(0, (window.winfo_width() - width) // 2)
        y = window.winfo_rooty() + max(0, (window.winfo_height() - height) // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.lift()
        try:
            dialog.grab_set()
        except Exception:
            pass
        dialog.update()
        return dialog

    @staticmethod
    def _close_saving_dialog(dialog):
        if dialog is None:
            return
        try:
            dialog.grab_release()
        except Exception:
            pass
        try:
            dialog.destroy()
        except Exception:
            pass

    def save(self):
        """Guarda, con el mismo nombre base, el PNG y un TXT con posición/jugadas."""
        filename = filedialog.asksaveasfilename(
            title="Guardar imagen del tablero y jugadas",
            defaultextension=".png",
            filetypes=[("Imagen PNG", "*.png")],
            initialfile="chess.png"
        )
        if not filename:
            return

        png_path = Path(filename)
        if png_path.suffix.lower() != ".png":
            png_path = png_path.with_suffix(".png")
        moves_path = png_path.with_suffix(".txt")

        saving_dialog = self._show_saving_dialog([png_path, moves_path])
        try:
            self._save_png(png_path)
            moves_path.write_text(self._moves_text(), encoding="utf-8")
        except Exception as exc:
            self._close_saving_dialog(saving_dialog)
            messagebox.showerror("Error al guardar", str(exc))
            return
        finally:
            self._close_saving_dialog(saving_dialog)

    def _save_png(self, filename):
        """Exporta tablero + flechas debajo de piezas + X siempre encima."""
        assets = relative_to_assets("images/chess")
        image = self._board_background_pil().copy()
        source_square = BOARD_SOURCE_INNER / 8.0
        draw = ImageDraw.Draw(image)

        def display_row_col(index):
            row, col = divmod(index, 8)
            if self.flipped:
                row, col = 7 - row, 7 - col
            return row, col

        def source_center(index):
            row, col = display_row_col(index)
            return (
                BOARD_SOURCE_MARGIN + source_square * (col + 0.5),
                BOARD_SOURCE_MARGIN + source_square * (row + 0.5),
            )

        def draw_arrow(draw_obj, p1, p2, color, dashed):
            import math
            x1, y1 = p1
            x2, y2 = p2
            width = max(8, int(source_square * 0.10))
            if dashed:
                dx, dy = x2 - x1, y2 - y1
                length = math.hypot(dx, dy)
                if length > 0:
                    ux, uy = dx / length, dy / length
                    dash_len, gap = source_square * 0.20, source_square * 0.12
                    pos = 0.0
                    line_end = max(0.0, length - source_square * 0.16)
                    while pos < line_end:
                        end = min(pos + dash_len, line_end)
                        draw_obj.line(
                            (x1 + ux * pos, y1 + uy * pos,
                             x1 + ux * end, y1 + uy * end),
                            fill=color, width=width
                        )
                        pos += dash_len + gap
            else:
                draw_obj.line((x1, y1, x2, y2), fill=color, width=width)

            angle = math.atan2(y2 - y1, x2 - x1)
            head_len = source_square * 0.28
            head_half = source_square * 0.13
            bx = x2 - head_len * math.cos(angle)
            by = y2 - head_len * math.sin(angle)
            px = -math.sin(angle)
            py = math.cos(angle)
            draw_obj.polygon([
                (x2, y2),
                (bx + head_half * px, by + head_half * py),
                (bx - head_half * px, by - head_half * py),
            ], fill=color)

        # 1) Flechas: capa inferior a las piezas.
        for ann in self.arrow_annotations:
            draw_arrow(
                draw, source_center(ann["start"]), source_center(ann["end"]),
                ann["color"], ann["dashed"]
            )

        # 2) Piezas: siempre encima de las flechas.
        base_piece_size = int(source_square * 0.90)
        for logical_row in range(8):
            for logical_col in range(8):
                idx = 8 * logical_row + logical_col
                name = self.board[idx].get_name()
                if not name:
                    continue
                piece = Image.open(assets / "pieces96" / f"{name}.png").convert("RGBA")
                factor = PIECE_SIZE_ADJUST.get(name, PIECE_SIZE_ADJUST.get(name[0], 1.0))
                piece_size = max(1, int(round(base_piece_size * factor)))
                piece = piece.resize((piece_size, piece_size), Image.Resampling.LANCZOS)
                row, col = display_row_col(idx)
                x = int(BOARD_SOURCE_MARGIN + col * source_square + (source_square - piece_size) / 2)
                y = int(BOARD_SOURCE_MARGIN + row * source_square + (source_square - piece_size) / 2)
                image.alpha_composite(piece, (x, y))

        # 3) X: capa superior a todo, incluso a las piezas.
        draw = ImageDraw.Draw(image)
        x_width = max(8, int(source_square * 0.10))
        x_margin = source_square * 0.22
        for ann in self.xmark_annotations:
            row, col = display_row_col(ann["index"])
            x0 = BOARD_SOURCE_MARGIN + col * source_square
            y0 = BOARD_SOURCE_MARGIN + row * source_square
            x1 = x0 + source_square
            y1 = y0 + source_square
            draw.line((x0 + x_margin, y0 + x_margin, x1 - x_margin, y1 - x_margin),
                      fill=ann["color"], width=x_width)
            draw.line((x0 + x_margin, y1 - x_margin, x1 - x_margin, y0 + x_margin),
                      fill=ann["color"], width=x_width)

        image.convert("RGB").save(str(filename), "PNG", optimize=True)

    def save_play_history(self):
        """Guarda manualmente un TXT con la misma información de jugadas/posición."""
        filename = filedialog.asksaveasfilename(
            title="Guardar jugadas",
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt")],
            initialfile="jugadas.txt"
        )
        if filename:
            path = Path(filename)
            saving_dialog = self._show_saving_dialog(path)
            try:
                path.write_text(self._moves_text(), encoding="utf-8")
            except Exception as exc:
                self._close_saving_dialog(saving_dialog)
                messagebox.showerror("Error al guardar", str(exc))
                return
            finally:
                self._close_saving_dialog(saving_dialog)

    def set_fila(self, x_i, x_j, color):
        pieces = ["T", "C", "A", "D", "R", "A", "C", "T"]
        for i in range(8):
            self.board[i + x_i].set_piece(pieces[i], color)
        for i in range(8):
            self.board[i + x_j].set_piece("p", color)

    def set_initial_board(self):
        self.set_empty_board()
        self.set_fila(0, 8, "N")
        self.set_fila(56, 48, "B")

    def clean(self):
        self.clear_annotations()
        canvas.delete('all')
        for box in self.board:
            box.clean()
        self.board = []
        self.board_background_id = None
        self.board_background_img = None
