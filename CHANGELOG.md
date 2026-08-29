# Changelog

## Versión editorial / refactor final

- Sustitución de piezas basadas en caracteres por PNG transparentes.
- Nuevo tablero gráfico y exportación PNG de alta calidad.
- Guardado conjunto PNG + TXT con el mismo nombre.
- Lectura y validación FEN, incluyendo TXT generados por el programa.
- El editor FEN muestra inicialmente la posición actual para poder copiarla.
- Rotación del tablero y selector de turno.
- Flechas configurables por color y estilo.
- Marcas X configurables por color.
- Historial común de anotaciones para borrar en el orden real de creación.
- Orden de capas unificado: flechas debajo de piezas y X encima.
- Organización de herramientas por secciones, hints e iconos con estado invertido.
- Ventana no modal de progreso durante el guardado.
- Escala visual homogénea de piezas.
- MySQL convertido en dependencia funcionalmente opcional.
- Credenciales MySQL retiradas del código y sustituidas por variables de entorno.
- Formato interno único para piezas (`RB`, `DN`, `pB`, etc.).
- Compatibilidad de lectura con registros antiguos (`RB0`, `RB1`, etc.).
- PGN, FEN, edición manual y tarjetero pasan por la misma normalización.
- Limpieza de imports globales y eliminación de recursos generados/obsoletos.
- Corrección y simplificación del módulo de búsqueda de patrones.
