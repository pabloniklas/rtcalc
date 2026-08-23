# RollTape Calculator

Calculadora simple en Python + PyQt5 con display LCD, una cinta (roller tape) que
registra las operaciones y sus resultados, y teclado numérico completo.

## Características

- **Interfaz**:
  - LCD que muestra los números en edición y el resultado.
  - Roller tape con el historial de la operación en curso.
  - Teclado: dígitos, `000`, separador decimal local, `+ - × ÷`, `=`,
    `±`, `Back`, `CE`, `C`, `CT` y memoria (`MC`, `MR`, `MS`, `M+`).
- **Funcionamiento**:
  - Separador decimal según la configuración regional del sistema.
  - Encadenado: tras `=` el resultado queda disponible para seguir operando;
    escribir un dígito inicia un cálculo nuevo.
  - Errores (por ejemplo división por cero) se muestran como `Error`
    conservando el estado para corregir la entrada.
  - Barra de estado con memoria activa y total parcial de la expresión.

## Atajos de teclado

| Tecla | Acción |
| --- | --- |
| `0-9`, `.`, `,` | Ingresar dígitos / separador decimal |
| `+ - * /` | Operaciones |
| `Enter`, `=` | Calcular resultado |
| `Backspace` | Borrar último carácter |
| `Esc` | Borrar todo (C) |
| `Supr` | Borrar entrada (CE) |
| `Ctrl+M` / `Ctrl+P` | Guardar en memoria (MS) / Sumar a memoria (M+) |
| `Ctrl+R` / `Ctrl+L` | Recordar memoria (MR) / Limpiar memoria (MC) |
| `Ctrl+C` / `Ctrl+V` | Copiar / pegar del portapapeles |

## Instalación

Se necesita Python 3 y PyQt5. `qtawesome` es opcional (solo agrega el ícono
de backspace):

```bash
pip install PyQt5 qtawesome
python3 rollcalc.py
```

## Ejecutable independiente

Con el spec incluido (recomendado; genera un onefile sin consola en `dist/rollcalc`):

```bash
pip install pyinstaller
pyinstaller --clean --noconfirm rollcalc.spec
./dist/rollcalc
```

O equivalentemente desde cero:

```bash
pyinstaller --onefile --windowed \
  --add-data "MPLUS1Code-Regular.ttf:." --add-data "rollcalc.png:." \
  rollcalc.py
```

Nota: en Windows reemplazar `:` por `;` en los `--add-data`.

## Pendiente

Gestión de eventos de mouse sobre la cinta (hoy funciona bien con teclado y botones).
