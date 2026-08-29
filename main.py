"""Punto de entrada de IA_Ajedrez."""

from tkinter import Button, PhotoImage

from src.chess.interfaceChess import InterfaceChess
from src.common.config import canvas, relative_to_assets, window
from src.common.interface import Interface
from src.elo.interfaceElo import InterfaceElo


class Home(Interface):
    """Pantalla principal de acceso al editor de ajedrez y la calculadora Elo."""

    def __init__(self) -> None:
        button_info = [
            ("jugar", self.set_game),
            ("calcular ELO", self.set_elo),
        ]
        super().__init__(button_info)
        self.interface_chess = InterfaceChess(self.set_home)
        self.interface_elo = InterfaceElo(self.set_home)

    def set_home(self):
        """Muestra las opciones principales."""
        canvas.place(x=0, y=0)
        canvas.create_rectangle(
            0.0,
            0.0,
            385.0,
            562.0,
            fill="#37B5D0",
            outline="",
        )

        for index in range(2):
            image = PhotoImage(
                file=relative_to_assets(f"images/{self.button_name[index][0]}.png")
            )
            self.img_buttons.append(image)
            button = Button(
                image=image,
                borderwidth=0,
                highlightthickness=0,
                command=self.button_name[index][1],
                relief="flat",
            )
            self.buttons.append(button)
            button.place(
                x=85.0 + (385 * index),
                y=260.0,
                width=212.0,
                height=49.0,
            )

    def set_game(self):
        """Abre el editor de diagramas de ajedrez."""
        self.clean()
        self.interface_chess.set_ornaments()
        self.interface_chess.set_play_history()
        self.interface_chess.create_buttons()
        canvas.bind("<Button-1>", self.interface_chess.click)
        self.interface_chess.set_board()

    def set_elo(self):
        """Abre la calculadora de rating Elo."""
        self.clean()
        self.interface_elo.set_text()
        self.interface_elo.set_buttons()


def main() -> None:
    home = Home()
    home.set_home()
    window.resizable(False, False)
    window.mainloop()


if __name__ == "__main__":
    main()
