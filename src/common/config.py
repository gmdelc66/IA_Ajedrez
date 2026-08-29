"""Configuración global de la interfaz y servicios opcionales.

El editor no necesita MySQL para funcionar. La conexión del tarjetero se
intenta únicamente con la configuración indicada mediante variables de
entorno. Esto evita guardar credenciales dentro del repositorio.
"""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import Canvas, Tk

OUTPUT_PATH = Path(__file__).resolve().parents[2]
ASSETS_PATH = OUTPUT_PATH / "assets"

# ---------------------------------------------------------------------------
# Base de datos opcional (tarjetero)
# ---------------------------------------------------------------------------
db = None
DB_AVAILABLE = False
DB_ERROR = None

try:
    import pymysql

    db = pymysql.connect(
        host=os.getenv("CHESSCARD_DB_HOST", "localhost"),
        port=int(os.getenv("CHESSCARD_DB_PORT", "3306")),
        user=os.getenv("CHESSCARD_DB_USER", "root"),
        password=os.getenv("CHESSCARD_DB_PASSWORD", ""),
        database=os.getenv("CHESSCARD_DB_NAME", "ChessCard"),
        connect_timeout=1,
    )
    DB_AVAILABLE = True
except Exception as exc:  # MySQL es opcional.
    DB_ERROR = exc

# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 850
WINDOW_HEIGHT = 640

window = Tk()
window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
window.configure(bg="#FFFFFF")

canvas = Canvas(
    window,
    bg="#FFFFFF",
    height=WINDOW_HEIGHT,
    width=WINDOW_WIDTH,
    bd=0,
    highlightthickness=0,
    relief="ridge",
)


def relative_to_assets(path: str) -> Path:
    """Devuelve una ruta absoluta dentro de ``assets``."""
    return ASSETS_PATH / path
