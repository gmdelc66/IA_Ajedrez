from tkinter import messagebox
from ..common.config import db, DB_AVAILABLE, DB_ERROR


class CardHolder:
    """Tarjetero de posiciones.

    El almacenamiento en MySQL es opcional. Si no existe un servidor MySQL
    local, el editor de tablero sigue funcionando; únicamente las funciones
    de guardar/ver tarjetas en la base de datos quedan desactivadas.
    """

    def __init__(self) -> None:
        self.cursor = db.cursor() if DB_AVAILABLE and db is not None else None
        self.all_cards = []

    def _database_unavailable(self):
        detail = f"\n\nDetalle: {DB_ERROR}" if DB_ERROR else ""
        messagebox.showwarning(
            "Base de datos no disponible",
            "El editor de tablero y la exportación PNG funcionan sin MySQL.\n"
            "El tarjetero requiere un servidor MySQL local configurado."
            + detail,
        )

    def add_card(self, titulo, tablero, descripcion):
        """Guarda una tarjeta en MySQL cuando la base está disponible."""
        if self.cursor is None:
            self._database_unavailable()
            return self.all_cards
        sql = "INSERT INTO jugadas(titulo, tablero, descripcion) VALUES (%s,%s,%s)"
        try:
            self.cursor.execute(sql, (titulo, tablero, descripcion))
            db.commit()
            messagebox.showinfo("Information", "Agregado con éxito")
            return self.get_all_cards()
        except Exception as exc:
            db.rollback()
            messagebox.showerror("Error", f"No se pudo guardar la tarjeta.\n\n{exc}")
            return self.all_cards

    def delete_card(self, id):
        """Elimina una tarjeta de MySQL."""
        if self.cursor is None:
            self._database_unavailable()
            return self.all_cards
        try:
            self.cursor.execute("DELETE FROM jugadas WHERE id=%s", (id,))
            db.commit()
            messagebox.showinfo("Information", "Eliminado con éxito")
            return self.get_all_cards()
        except Exception as exc:
            db.rollback()
            messagebox.showerror("Error", f"No se pudo eliminar la tarjeta.\n\n{exc}")
            return self.all_cards

    def update_card(self, id, titulo, tablero, descripcion):
        """Actualiza una tarjeta de MySQL."""
        if self.cursor is None:
            self._database_unavailable()
            return self.all_cards
        sql = "UPDATE jugadas SET titulo=%s, tablero=%s, descripcion=%s WHERE id=%s"
        try:
            self.cursor.execute(sql, (titulo, tablero, descripcion, id))
            db.commit()
            messagebox.showinfo("Information", "Actualizado con éxito")
            return self.get_all_cards()
        except Exception as exc:
            db.rollback()
            messagebox.showerror("Error", f"No se pudo actualizar la tarjeta.\n\n{exc}")
            return self.all_cards

    def get_all_cards(self):
        """Regresa las tarjetas almacenadas; vacío si MySQL no está disponible."""
        if self.cursor is None:
            self.all_cards = []
            return self.all_cards
        try:
            self.cursor.execute("SELECT * FROM jugadas")
            self.all_cards = self.cursor.fetchall()
        except Exception:
            self.all_cards = []
        return self.all_cards
