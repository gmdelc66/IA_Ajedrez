from tkinter.constants import LEFT, WORD
from .cardHolder import CardHolder
from src.common.interface import Interface
from tkinter import messagebox, Text, PhotoImage, Button, Label
#Para generar el pdf
from src.common.config import canvas, relative_to_assets
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.lib.styles import ParagraphStyle

class InterfaceCardH(Interface):
    """
    InterfaceCardH

    Crea una interfaz para que el usuario pueda 
    agregar, modificar, buscar y ver jugadas 
    """
    def __init__(self, set_home, board, menu) -> None:
        #Home
        self.set_home = set_home
        self.id = ["",]
        #Tablero
        self.board = board 
        #Menu
        self.set_menu = menu.set_menu
        self.menu = menu
        #Base de datos
        self.card_holder = CardHolder()
        self.cards = self.card_holder.get_all_cards()
        self.holder_card = []
        #Para los rectángulos de todas las cartas
        self.rec = []
        #Número de página para ver las tarjetas
        self.page = 0
        #Para que el usuario ingrese los valores
        self.entry_img = []
        self.entry = []
        #Img botón ver
        self.look = PhotoImage(
            file=relative_to_assets("images/elo/ver.png"))
        #Para el PDF
        font = "assets/fonts/MERIFONT.TTF"
        pdfmetrics.registerFont(TTFont('ChessMerida', font))
        self.pdf = SimpleDocTemplate("chessCard.pdf")
        #Botones y su función al dar click
        self.button_info = [("regresar", self.back),
                       ("home", self.go_home),
                       ("guardar", self.save),
                       ("editar", self.set_menu),
                       ("borrar", self.delete),
                       ("descargar", self.pdf_card),
                       ("regresar", lambda : self.next_card(-5)),
                       ("agregar", lambda : self.card_on_click("", True)),
                       ("siguiente", lambda : self.next_card(5))]
        super().__init__(self.button_info)

    def pdf_card(self):
        tablero = self.board.to_string()
        board_style = ParagraphStyle(
            "Board",
            fontName="ChessMerida",
            alignment=TA_CENTER,
            leading=30,
            fontSize=30
        )
        title_style = ParagraphStyle(
            "Title",
            fontName="Helvetica",
            alignment=TA_CENTER,
            leading=50,
            fontSize=20
        )
        text_style = ParagraphStyle(
            "Text",
            fontName="Helvetica",
            alignment=TA_JUSTIFY,
            fontSize=12
        )
        self.pdf.build([Paragraph(self.cards[self.id[1]][1], title_style),
                        Paragraph(self.cards[self.id[1]][3], text_style),
                        Paragraph(tablero, board_style)])

        messagebox.showinfo("Information","Tarjeta guardada en chessCard.pdf")

    def move_to_window(self):   
        """Limpia la ventana y prepara todo para la siguiente"""
        self.clean()
        self.page = 0
        self.set_footer()
        self.set_header()
        self.default_buttons()

    def show_cards(self):
        """Muestra todas las tarjetas de jugadas almacenadas 
        en la base de datos"""
        self.move_to_window()
        #Rectángulo para jugadas
        self.rec.append(canvas.create_rectangle(
            66,
            155,
            704,
            480,
            fill="#E5E5E5",
            outline=""))
        for i in range(3):
            #Para agregar una o ver más
            self.buttons[i+6].place(
                x=150 + (i*200),
                y=492,
                width=40 if i != 1 else 85,
                height=40 if i != 1 else 24,
            )
        #Primeras 5
        self.next_card(5)

    def next_card(self, num):
        """Limpia la página actual y pone las tarjetas
        correspondientes a la nueva página"""
        num = self.page + num
        num = num if len(self.cards) > num else len(self.cards)
        num = num if num > 0 else 0
        
        a = num if num < self.page else self.page
        b = self.page if num < self.page else num
        k = 0
        for i in range(len(self.holder_card)):
            self.holder_card[i][0].destroy()
            self.holder_card[i][1].destroy()
            self.holder_card[i][2].destroy()

        for j in range(b-a):
            self.set_one_card(a+j, k*65)
            k+=1
        self.page = b - 1

    def set_one_card(self, i, k):
        """Muestra la información de una tarjeta de juego
        i - id de la tarjeta"""
        move = []
        description = self.cards[i][3]
        if len(description) > 13:
            description = self.cards[i][3][0:10]+"..."
        move.append(Label(
                text=str(i)+" "+self.cards[i][1],
                bg="#E5E5E5",
                justify=LEFT)) #Título
        move.append(Label(
            text=description,
            bg="#E5E5E5",
            justify=LEFT)) #Descripción
        move[0].place(x=81, y=175 + k)
        move[1].place(x=301, y=172 + k)
        move.append(Button(
                image=self.look,
                borderwidth=0,
                highlightthickness=0,
                command= lambda id = i: self.card_on_click(id),
                relief="flat"
        ))
        move[2].place(
            x=602,
            y=179 + k,
            width=70.7,
            height=20
        )
        self.holder_card.append(move)
        

    def card_on_click(self,id, new=False):
        """Nos muestra otra vista para editar, guardar, eliminar
        la tarjeta
        id - Id de la jugada"""
        self.move_to_window()
        self.set_buttons()
        #Rectángulo detrás del tablero
        canvas.place(x = 0, y = 0)
        canvas.create_rectangle(
            34.0,
            92.0,
            410.6521301269531,
            477.90203857421875,
            fill="#C4C4C4",
            outline="")
        self.board.set_board_num()
        self.board.set_board_letters()
        if new:
            self.id = ["",]
            self.set_entry() #Mostramos las tarjeta
            self.board.set_empty_board()
        else:
            self.id = [self.cards[id][0],id]
            self.set_entry(self.cards[id][1],self.cards[id][3]) #Mostramos las tarjeta
            self.board.set_board(self.cards[id][2].split())

    def save(self):
        """Guarda en la base de datos la información
        de la tarjeta"""
        tablero = self.board.get_coord()
        titulo = self.entry[0].get(1.0,'end')
        descripcion = self.entry[1].get(1.0,'end')
        if self.id[0] == "":
            self.cards = self.card_holder.add_card(titulo, tablero, descripcion)
        else:
            self.cards = self.card_holder.update_card(self.id[0],titulo, tablero, descripcion)

    def delete(self):
        """Borra una tarjeta de la base de datos, no regresa a ver todas las 
        jugadas"""
        self.cards = self.card_holder.delete_card(self.id[0]) 
        self.clean()
        self.show_cards()

    def set_entry(self, titulo = '''Título''',  descripcion = '''Descripción'''):
        #Rectángulo para jugadas
        canvas.create_rectangle(
            432.0,
            98.0,
            599.0,
            473.0,
            fill="#FFFFFF",
            outline="")

        for i in range(2):
            self.entry.append(Text(
                width = 253, 
                height = 35 + (i*189), 
                wrap = WORD,
                padx = 5,
                pady = 5))

            self.entry[i].place(
                x=462,
                y=110 + (i*60),
                width=253,
                height=35 + (i*189)
            )
            self.entry[i].insert('1.0',titulo if i == 0 else descripcion)
            
    def clean(self):
        """Eliminamos todo lo del canvas"""
        super().clean()
        if len(self.entry) != 0:
            for i in self.entry:
                i.destroy()
        for i in self.holder_card:
            for j in i:
                j.destroy()
        self.holder_card = []
        self.entry = []
        self.board.clean()
        self.menu.clean()

    def default_buttons(self):
        """Agrega imágenes de adorno y para regresar a la
        página anterior o al inicio"""
        self.set_footer()
        self.set_header()
        
        for i in range(len(self.button_info)):
            self.img_buttons.append(PhotoImage(
            file=relative_to_assets("images/elo/"+self.button_info[i][0] + ".png")))
            self.buttons.append(Button(
                image=self.img_buttons[i],
                borderwidth=0,
                highlightthickness=0,
                command=self.button_info[i][1],
                relief="flat"
            ))
        for i in range(2):
            self.buttons[i].place(
                x=47 + (i * 621),
                y=37,
                width=40,
                height=40
            )

    def set_buttons(self):
        """Agrega los botones para editar, guardar, eliminar y descargar"""
        
        for i in range(4):
            self.buttons[i+2].place(
                x=462 + (i*131) if i < 2 else 462 + ((i-2)*131),
                y=422 if i < 2 else 464,
                width=117.41,
                height=29.89
            )

    def back(self):
        """Nos regresa a la vista de todas las tarjetas"""
        self.clean()
        self.show_cards()

    def go_home(self):
        """Regresa al usuario a la página principal"""
        self.clean()
        self.set_home()
