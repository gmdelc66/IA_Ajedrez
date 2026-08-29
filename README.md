# IA_Ajedrez — editor de diagramas y herramientas de ajedrez

Este proyecto es una evolución del repositorio original **IA_Ajedrez** de
[KarlaDSJ](https://github.com/KarlaDSJ/IA_Ajedrez). Se conserva la idea y la
estructura general del trabajo original, pero el editor de diagramas fue
modernizado para facilitar la creación de material didáctico y editorial.

> **Crédito del proyecto original:** KarlaDSJ / IA_Ajedrez.  
> Esta versión no añade una licencia nueva al código original; antes de una
> redistribución distinta de un fork o contribución al proyecto, conviene
> conservar las condiciones que establezca la autora del repositorio original.

## Funciones principales

### Editor de diagramas

- Tablero gráfico con piezas PNG, sin caracteres ASCII/Unicode para dibujar las piezas.
- Colocación y movimiento manual de piezas.
- Flechas de colores, continuas o punteadas.
- Marcas **X** de colores.
- Capas consistentes al exportar: **flechas → piezas → marcas X**.
- Rotación del tablero para ver la posición desde blancas o negras.
- Selector de turno: **ON = Blancas / OFF = Negras**.
- Lectura, edición, copiado y validación de posiciones **FEN**.
- Lectura de archivos `.fen`, `.txt` o cualquier archivo que contenga una línea FEN.
- Lectura y navegación de partidas **PGN**.
- Exportación simultánea de imagen `.png` y archivo `.txt` con el mismo nombre base.
- El TXT guardado incluye FEN, turno y jugadas disponibles.
- Ventana temporal de progreso durante el guardado.
- Hints en los botones y estado visual invertido para la herramienta seleccionada.

### Herramientas heredadas del proyecto original

- Calculadora de rating Elo.
- Tarjetero de posiciones con MySQL (opcional).
- Búsqueda de patrones en partidas PGN.

## Representación interna de piezas

Para evitar los errores de compatibilidad que existían entre FEN, PGN y el
tarjetero, toda la aplicación utiliza ahora **un único formato interno**:

```text
RB DB TB AB CB pB   # blancas: rey, dama, torre, alfil, caballo, peón
RN DN TN AN CN pN   # negras
```

Las casillas vacías son `""` en memoria y `--` al serializar el tarjetero.

Las versiones antiguas guardaban valores como `RB0` o `RB1`, mezclando la
identidad de la pieza con el color de la casilla. Esta versión puede **leer**
esos registros por compatibilidad, pero los normaliza inmediatamente al
formato de dos caracteres. De esa manera FEN, PGN, edición manual y tarjetero
comparten exactamente la misma representación.

## Requisitos

- Python 3.9 o posterior.
- Tkinter instalado en el sistema.
- Pillow.
- python-chess (`chess`).
- ReportLab.
- PyMySQL, únicamente para el tarjetero MySQL.

En Ubuntu/Debian, si Tkinter no está instalado:

```bash
sudo apt install python3-tk
```

## Instalación recomendada

```bash
git clone https://github.com/KarlaDSJ/IA_Ajedrez.git
cd IA_Ajedrez
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para ejecutar:

```bash
python main.py
```

También puede ejecutarse sin activar previamente el entorno:

```bash
./.venv/bin/python main.py
```

## Tarjetero MySQL (opcional)

El editor, FEN, PGN y la exportación de imágenes **no necesitan MySQL**.
Para usar el tarjetero:

```bash
mysql -u root -p < DDL.sql
```

Las credenciales ya no están escritas dentro del código. Se leen de variables
de entorno:

```text
CHESSCARD_DB_HOST
CHESSCARD_DB_PORT
CHESSCARD_DB_USER
CHESSCARD_DB_PASSWORD
CHESSCARD_DB_NAME
```

Puede copiar `.env.example` como referencia. El programa funciona normalmente
si MySQL no está disponible; sólo las operaciones del tarjetero quedan
deshabilitadas.

## FEN

El botón **Pegar o leer archivo FEN** abre un editor que comienza mostrando el
FEN de la posición actual. Esto permite copiarlo directamente o sustituirlo por
otro.

El lector acepta:

```text
3k4/3q4/8/1pp1p3/2PP4/8/5PP1/3K4 w - - 0 1
```

También reconoce el formato TXT generado por el propio programa:

```text
Posición (FEN):
3k4/3q4/8/1pp1p3/2PP4/8/5PP1/3K4 w - - 0 1

Juegan: Blancas
```

## Exportación

Al guardar, por ejemplo:

```text
mov_peon.png
```

se crean:

```text
mov_peon.png
mov_peon.txt
```

Las anotaciones se exportan respetando el mismo orden visual de la pantalla:
las flechas quedan debajo de las piezas y las marcas X encima.

## Compatibilidad

El módulo `src/chess/pieces.py` es la única fuente de verdad para nombres de
piezas, conversión FEN/python-chess, escalas visuales y normalización de datos
heredados. Si se agrega una nueva función relacionada con posiciones, debe
usar ese módulo en lugar de crear otra tabla de equivalencias.

## Estructura relevante

```text
src/chess/board.py      tablero, FEN, anotaciones y exportación
src/chess/box.py        casillas y render de piezas PNG
src/chess/menu.py       herramientas de edición
src/chess/pgn.py        lectura y navegación PGN
src/chess/pieces.py     formato canónico y conversiones de piezas
src/chess/pattern.py    búsqueda de patrones
src/common/config.py    interfaz global y MySQL opcional
assets/images/chess/    tablero, iconos y piezas
```

## Agradecimiento

Gracias a **KarlaDSJ** por publicar el código original que hizo posible esta
versión. La intención de esta revisión es devolver al proyecto una edición más
robusta, coherente y práctica para crear diagramas de ajedrez.
