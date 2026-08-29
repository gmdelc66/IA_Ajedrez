"""Representación canónica de piezas usada por todo el editor.

Formato interno
---------------
Cada pieza se representa SIEMPRE con dos caracteres::

    RB DB TB AB CB pB   # blancas
    RN DN TN AN CN pN   # negras

La primera letra identifica la pieza (R, D, T, A, C, p) y la segunda el
color (B = blancas, N = negras). Las casillas vacías se representan con la
cadena vacía ``""``.

Las versiones antiguas del proyecto añadían ``0`` o ``1`` al final para
codificar el color de la casilla (por ejemplo ``RB0``). Ese dato pertenece al
tablero, no a la pieza. ``normalize_piece_id`` acepta ese formato únicamente
en las fronteras de compatibilidad, pero dentro del programa se usa siempre
el formato de dos caracteres.
"""

from __future__ import annotations

from typing import Iterable, List

import chess

WHITE_IDS = ("RB", "DB", "TB", "AB", "CB", "pB")
BLACK_IDS = ("RN", "DN", "TN", "AN", "CN", "pN")
PIECE_IDS = frozenset(WHITE_IDS + BLACK_IDS)
EMPTY_TOKEN = "--"

FEN_TO_PIECE = {
    "K": "RB",
    "Q": "DB",
    "R": "TB",
    "B": "AB",
    "N": "CB",
    "P": "pB",
    "k": "RN",
    "q": "DN",
    "r": "TN",
    "b": "AN",
    "n": "CN",
    "p": "pN",
}

PIECE_TO_FEN = {value: key for key, value in FEN_TO_PIECE.items()}

CHESS_TO_PIECE = {
    (chess.KING, chess.WHITE): "RB",
    (chess.QUEEN, chess.WHITE): "DB",
    (chess.ROOK, chess.WHITE): "TB",
    (chess.BISHOP, chess.WHITE): "AB",
    (chess.KNIGHT, chess.WHITE): "CB",
    (chess.PAWN, chess.WHITE): "pB",
    (chess.KING, chess.BLACK): "RN",
    (chess.QUEEN, chess.BLACK): "DN",
    (chess.ROOK, chess.BLACK): "TN",
    (chess.BISHOP, chess.BLACK): "AN",
    (chess.KNIGHT, chess.BLACK): "CN",
    (chess.PAWN, chess.BLACK): "pN",
}

PIECE_LABELS = {
    "R": "rey",
    "D": "dama",
    "T": "torre",
    "A": "alfil",
    "C": "caballo",
    "p": "peón",
}

# Ajustes puramente visuales para igualar el tamaño aparente de los PNG.
PIECE_SIZE_ADJUST = {
    "T": 0.90,
    "pN": 0.91,
}


def normalize_piece_id(value: object) -> str:
    """Devuelve un identificador canónico de dos caracteres.

    Acepta datos heredados como ``RB0``/``RB1`` y tokens vacíos usados por
    versiones anteriores. Se lanza ``ValueError`` si el token no representa
    una pieza conocida.
    """
    if value is None:
        return ""

    token = str(value).strip()
    if token in ("", EMPTY_TOKEN, "0", "1", "."):
        return ""

    if len(token) == 3 and token[-1] in "01":
        token = token[:2]

    if token not in PIECE_IDS:
        raise ValueError(f"Identificador de pieza no válido: {value!r}")
    return token


def normalize_position(values: Iterable[object]) -> List[str]:
    """Normaliza una posición de exactamente 64 casillas."""
    result = [normalize_piece_id(value) for value in values]
    if len(result) != 64:
        raise ValueError(f"Una posición debe contener 64 casillas; recibió {len(result)}.")
    return result


def chess_board_to_position(board: chess.Board) -> List[str]:
    """Convierte ``python-chess`` a la representación interna de 64 casillas."""
    result: List[str] = []
    for row in range(8):
        rank = 7 - row
        for col in range(8):
            piece = board.piece_at(chess.square(col, rank))
            if piece is None:
                result.append("")
            else:
                result.append(CHESS_TO_PIECE[(piece.piece_type, piece.color)])
    return result


def serialize_position(values: Iterable[object]) -> str:
    """Serializa 64 casillas en un formato estable para el tarjetero."""
    return " ".join(normalize_piece_id(value) or EMPTY_TOKEN for value in values)
