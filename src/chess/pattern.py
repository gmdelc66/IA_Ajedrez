"""Búsqueda de patrones sencillos dentro de partidas PGN."""

from __future__ import annotations

from tkinter import Button, Entry, Label, Toplevel, messagebox

import chess

from src.common.config import canvas


class Pattern:
    """Busca patrones de piezas/ataques dentro de una colección de partidas."""

    def __init__(self, games, board_set_board, parse) -> None:
        self.patterns = []
        self.games = games
        self.board_set_board = board_set_board
        self.parse = parse

    def read_file(self):
        """Solicita la ruta del archivo que contiene los patrones."""
        level = Toplevel(canvas)
        level.geometry("300x200")
        Label(level, text="Ruta del archivo con el patrón:").place(x=10, y=10)
        name_arch = Entry(level, width=30)
        name_arch.insert(0, "patron.txt")
        name_arch.place(x=30, y=50)
        Button(
            level,
            text="Leer",
            command=lambda: (self.get_pattern(name_arch.get()), level.destroy()),
        ).place(x=120, y=80)

    def get_pattern(self, name):
        """Lee el archivo de patrones y ejecuta la búsqueda."""
        try:
            with open(name, encoding="utf-8", errors="replace") as pattern_file:
                self.patterns = [
                    line.strip().split(", ")
                    for line in pattern_file
                    if line.strip()
                ]
        except OSError:
            messagebox.showerror("Error", "Archivo no encontrado")
            return

        boards, games = self.search_pattern()
        if not boards:
            messagebox.showerror("Error", "Patrón no encontrado")
            return

        self.board_set_board(self.parse(boards[0]))
        games_text = ", ".join(map(str, games))
        messagebox.showinfo("Información", f"Patrón encontrado en los juegos: [{games_text}]")

    @staticmethod
    def _matches_piece(piece, symbol: str) -> bool:
        """Comprueba tipo y color usando la notación estándar de python-chess."""
        if piece is None or not symbol:
            return False
        try:
            expected = chess.Piece.from_symbol(symbol)
        except ValueError:
            return False
        return piece.piece_type == expected.piece_type and piece.color == expected.color

    def attack_by(self, expression: str, board: chess.Board) -> bool:
        """Evalúa expresiones del tipo ``B(h7)`` (una pieza ataca h7)."""
        symbol, square_text = expression.split("(", 1)
        square = chess.parse_square(square_text[:-1])
        color = symbol.isupper()
        return any(
            self._matches_piece(board.piece_at(square_id), symbol)
            for square_id in board.attackers(color, square)
        )

    def _matches_expression(self, expression: str, board: chess.Board) -> bool:
        if "(" in expression:
            return self.attack_by(expression, board)
        if len(expression) < 3:
            return False
        symbol = expression[0]
        square = chess.parse_square(expression[1:])
        return self._matches_piece(board.piece_at(square), symbol)

    def search_pattern(self):
        """Devuelve posiciones y números de partida donde aparece un patrón."""
        found_boards = []
        found_games = []

        for game_index, game in enumerate(self.games):
            moves = list(game.mainline_moves())
            for pattern in self.patterns:
                board = game.board()
                for move in moves:
                    if all(self._matches_expression(expr, board) for expr in pattern):
                        found_boards.append(board.copy())
                        found_games.append(game_index)
                        break
                    board.push(move)

        return found_boards, found_games
