from tkinter import PhotoImage, Toplevel, Label
from .config import canvas, relative_to_assets


class ToolTip:
    """Hint sencillo que aparece al dejar el puntero sobre un botón."""
    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip = None
        self.after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        try:
            self.after_id = self.widget.after(self.delay, self._show)
        except Exception:
            self.after_id = None

    def _cancel(self):
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _show(self):
        self.after_id = None
        if self.tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
            y = self.widget.winfo_rooty() + 4
            self.tip = Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            Label(
                self.tip, text=self.text, justify="left",
                background="#FFF7D6", foreground="#111111",
                relief="solid", borderwidth=1,
                font=("DejaVu Sans", 9), padx=6, pady=3
            ).pack()
        except Exception:
            self.tip = None

    def _hide(self, _event=None):
        self._cancel()
        if self.tip is not None:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None


class Interface:
    """
    Interface

    Crea una interfaz para que el usuario pueda interactuar
    """

    def __init__(self, button_info) -> None:
        self.button_name = button_info
        self.buttons = []
        self.img_buttons = []
        self.tooltips = []

    def clean(self, all=True):
        """Limpia el canvas y destruye widgets de la interfaz."""
        if all:
            canvas.delete('all')
        for i in self.buttons:
            try:
                i.destroy()
            except Exception:
                pass
        self.buttons = []
        self.img_buttons = []
        self.tooltips = []

    def set_footer(self):
        self.image_down_img = PhotoImage(
            file=relative_to_assets("images/ola_down.png"))
        self.image_down = canvas.create_image(
            385.0, 552.0, image=self.image_down_img
        )

    def set_header(self):
        self.image_top_img = PhotoImage(
            file=relative_to_assets("images/ola_top.png"))
        self.image_top = canvas.create_image(
            385.0, 10.0, image=self.image_top_img
        )
