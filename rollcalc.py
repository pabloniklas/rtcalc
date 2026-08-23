#!/usr/bin/env python3
"""
Roll Tape Calculator
By Pablo Niklas — 20240729

Empaquetado recomendado:
    pyinstaller --onefile --add-data "MPLUS1Code-Regular.ttf:." rollcalc.py
"""

import os
import sys
import ast
import operator as op

from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QTextEdit,
    QHBoxLayout, QSizePolicy, QStatusBar, QMenuBar, QAction, QMessageBox
)
from PyQt5.QtGui import QFont, QTextCursor, QIcon, QFontDatabase, QKeySequence
from PyQt5.QtCore import Qt, QLocale, QPropertyAnimation

try:
    import qtawesome as qta
except ImportError:
    qta = None

_VERSION = "1.1"

# --- util de evaluación segura (+ - * / y +/- unario) ------------------------
_ALLOWED_BINOPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
}
_ALLOWED_UNOPS = {ast.UAdd: op.pos, ast.USub: op.neg}
_OPERATORS = ("+", "-", "*", "/")


def _safe_eval(expr: str) -> float:
    """Evalúa expresión aritmética segura (solo + - * / y unarios)."""
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) \
                and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            return _ALLOWED_BINOPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNOPS:
            return _ALLOWED_UNOPS[type(node.op)](_eval(node.operand))
        raise ValueError("Operación no permitida")
    tree = ast.parse(expr, mode="eval")
    return float(_eval(tree))


def _format_token(value: float) -> str:
    """Float a token sin notación científica ni ceros colgantes."""
    s = f"{value:.12f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


# --- CPU ----------------------------------------------------------------------
class Cpu:
    """Lógica pura: trabaja internamente siempre con '.' como separador."""

    def __init__(self, decimal_point: str = "."):
        self._dec = decimal_point
        self._tempinput = ""     # buffer en edición ('.' interno)
        self._operation = []     # tokens: ["12", "+", "3", ...]
        self._result = None      # resultado encadenable tras '='
        self.memory = 0.0

    # --- buffer de entrada ---
    def buffer_append(self, x: str):
        s = str(x).replace(self._dec, ".")
        if len(s) > 1 and not s.isdigit():
            s = "".join(ch for ch in s if ch in "0123456789-.")
        if not s:
            return
        if "-" in s:             # pegado de un número con signo: reemplaza
            self._tempinput = s
            self._result = None
            return
        if self._result is not None:
            self._tempinput = ""
            self._result = None
        if self._tempinput in ("0", "-0") and s.isdigit():
            self._tempinput = "-" if self._tempinput == "-0" else ""
        if "." in s and "." in self._tempinput:
            s = s.replace(".", "")
        self._tempinput += s

    def buffer_reset(self):
        self._tempinput = ""

    def buffer_remove(self):
        if self._tempinput:
            self._tempinput = self._tempinput[:-1]

    def get_tempinput(self) -> str:
        return self._tempinput.replace(".", self._dec)

    def pending_token(self) -> str:
        """Operando pendiente: buffer actual o último resultado."""
        if self._tempinput != "":
            return self._tempinput
        if self._result is not None:
            return _format_token(self._result)
        return "0"

    def negate(self):
        if self._tempinput == "":
            if self._result is None:
                return
            self._tempinput = _format_token(self._result)
            self._result = None
        if self._tempinput.startswith("-"):
            self._tempinput = self._tempinput[1:]
        else:
            self._tempinput = "-" + self._tempinput

    # --- operaciones ---
    def _consume_operand(self) -> str:
        if self._tempinput != "":
            tok = self._tempinput
            self._tempinput = ""
            return tok
        if self._result is not None:
            tok = _format_token(self._result)
            self._result = None
            return tok
        return ""

    def _push_operator(self, symbol: str):
        operand = self._consume_operand()
        if operand:
            self._operation.append(operand)
        elif not self._operation:
            self._operation.append("0")
        if self._operation[-1] in _OPERATORS:
            self._operation[-1] = symbol
        else:
            self._operation.append(symbol)

    def add(self): self._push_operator("+")
    def sub(self): self._push_operator("-")
    def div(self): self._push_operator("/")
    def mul(self): self._push_operator("*")

    def reset(self):
        self._tempinput = ""
        self._operation = []
        self._result = None

    def get_operation_string(self) -> str:
        return " ".join(self._operation).replace(".", self._dec)

    # --- evaluación ---
    def _clean_tokens(self):
        tokens = list(self._operation)
        if self._tempinput != "":
            tokens.append(self._tempinput)
        elif self._result is not None:
            tokens.append(_format_token(self._result))
        while tokens and tokens[-1] in _OPERATORS:
            tokens.pop()
        return tokens

    def running_total(self) -> float:
        """Total parcial respetando operadores (para el status bar)."""
        tokens = self._clean_tokens()
        if not tokens:
            return 0.0
        try:
            return _safe_eval("".join(tokens))
        except Exception:
            return 0.0

    def evaluate(self) -> float:
        """Evalúa; propaga excepciones en error y encadena el resultado."""
        tokens = self._clean_tokens()
        if not tokens:
            return 0.0
        value = _safe_eval("".join(tokens))
        self.reset()
        self._result = value
        return value

    # --- memoria ---
    def memory_clear(self): self.memory = 0.0

    def memory_recall(self):
        self._tempinput = _format_token(self.memory)
        self._result = None

    def memory_store(self):
        try:
            self.memory = float(self.pending_token())
        except ValueError:
            pass

    def memory_add(self):
        try:
            self.memory += float(self.pending_token())
        except ValueError:
            pass


# --- UI -----------------------------------------------------------------------
class CalcFrame(QWidget):
    def __init__(self):
        super().__init__()
        self._dec = QLocale.system().decimalPoint()
        self.cpu = Cpu(self._dec)
        self._lcd_display_font_size = 15
        self._rollertape_font_size = 13
        self._key_font = QFont("Roboto Condensed", 15)
        self.button_map = {}
        self._animations = {}  # una animación viva por botón
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        # --- fuentes empaquetadas / fallback ---
        base = getattr(sys, "_MEIPASS", "")
        font_file = os.path.join(base, "MPLUS1Code-Regular.ttf") if base else "MPLUS1Code-Regular.ttf"
        font_id = QFontDatabase.addApplicationFont(font_file)
        if font_id == -1:
            roll_font = QFont("Roboto Mono", self._rollertape_font_size)  # fallback
        else:
            family = QFontDatabase.applicationFontFamilies(font_id)
            roll_font = QFont(family[0] if family else "Monospace", self._rollertape_font_size)

        # --- menús ---
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("QMenuBar { font-size: 12pt; } QMenu { font-size: 12pt; }")
        main_layout.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        exit_action = QAction(QIcon.fromTheme('application-exit'), "Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction(QIcon.fromTheme('edit-copy'), "Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_to_clipboard)
        paste_action = QAction(QIcon.fromTheme('edit-paste'), "Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        about_menu = menu_bar.addMenu("About")
        about_action = QAction(QIcon.fromTheme('help-about'), "About", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

        # --- top UI ---
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # izquierda: display + teclas
        left_layout = QVBoxLayout()
        top_layout.addLayout(left_layout)

        # display
        self.lcd_display = QTextEdit()
        self.lcd_display.setFont(QFont(roll_font.family(), self._lcd_display_font_size))
        self.lcd_display.setFixedHeight(40)
        self.lcd_display.setStyleSheet("background: rgb(255, 228, 181); color: black; border: 1px solid black;")
        self.lcd_display.setAlignment(Qt.AlignRight)
        self.lcd_display.setReadOnly(True)
        self.lcd_display.setFocusPolicy(Qt.NoFocus)
        left_layout.addWidget(self.lcd_display)

        # grid de botones (layout explícito, sin huecos)
        grid = QGridLayout()
        left_layout.addLayout(grid)

        rows = [
            [('Back', self.back), ('CE', self.clear_entry), ('C', self.clear),
             ('CT', self.clear_tape), ('MC', self.memory_clear)],
            [('7', self.enter_argument), ('8', self.enter_argument), ('9', self.enter_argument),
             ('/', self.div), ('MR', self.memory_recall)],
            [('4', self.enter_argument), ('5', self.enter_argument), ('6', self.enter_argument),
             ('*', self.mul), ('MS', self.memory_store)],
            [('1', self.enter_argument), ('2', self.enter_argument), ('3', self.enter_argument),
             ('-', self.sub), ('M+', self.memory_add)],
            [('0', self.enter_argument), ('000', self.enter_argument), (self._dec, self.enter_argument),
             ('±', self.negate), ('+', self.add)],
        ]
        for r, row in enumerate(rows):
            for c, (text, method) in enumerate(row):
                button = QPushButton(text)
                button.setFont(self._key_font)
                button.setFocusPolicy(Qt.NoFocus)
                self.button_map[text] = button
                if text == "Back":
                    if qta is not None:
                        button.setIcon(qta.icon('fa5s.backspace'))
                        button.setIconSize(QtCore.QSize(30, 30))
                        button.setText("")
                    button.setStyleSheet("background-color: #f04a50; border: 1px solid gray;")
                else:
                    button.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                button.clicked.connect(lambda _, x=text, m=method: self.on_button_click(x, m))
                grid.addWidget(button, r, c)

        # botón "=" a lo ancho
        equal_button = QPushButton("=")
        equal_button.setFont(self._key_font)
        equal_button.setFocusPolicy(Qt.NoFocus)
        equal_button.setStyleSheet("background-color: #6db442; border: 1px solid gray; color: white;")
        equal_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        equal_button.clicked.connect(lambda: self.on_button_click('=', self.evaluate))
        self.button_map['='] = equal_button
        grid.addWidget(equal_button, 5, 0, 1, 5)

        # estirar filas/columnas
        for i in range(6):
            grid.setRowStretch(i, 1)
        for j in range(5):
            grid.setColumnStretch(j, 1)

        # derecha: roller tape
        self.gui_rollertape = QTextEdit()
        self.gui_rollertape.setFont(roll_font)
        self.gui_rollertape.setReadOnly(True)
        self.gui_rollertape.setAlignment(Qt.AlignRight)
        self.gui_rollertape.setFocusPolicy(Qt.NoFocus)
        top_layout.addWidget(self.gui_rollertape)

        # status bar
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        self.update_status_bar()

        # ventana
        self.setWindowTitle('GNU Roll Tape Calc')
        self.resize(800, 400)
        self.setFixedSize(800, 400)
        icon_path = os.path.join(base, "rollcalc.png") if base else "rollcalc.png"
        self.window().setWindowIcon(QIcon(icon_path))

    # --- helpers UI ---
    def on_button_click(self, text, method):
        self.animate_button(text)
        method(text)

    def animate_button(self, text):
        button = self.button_map.get(text)
        if not button:
            return
        old = self._animations.pop(text, None)
        if old is not None:
            old.stop()
            old.deleteLater()
        original_style = button.styleSheet()
        animation = QPropertyAnimation(button, b"styleSheet", button)
        animation.setDuration(150)
        animation.setKeyValueAt(0, original_style)
        animation.setKeyValueAt(0.5, "background-color: yellow; border: 1px solid gray;")
        animation.setKeyValueAt(1, original_style)
        animation.finished.connect(lambda t=text: self._animations.pop(t, None))
        animation.finished.connect(animation.deleteLater)
        self._animations[text] = animation
        animation.start()

    def format_number(self, value: float) -> str:
        return QLocale.system().toString(value, 'f', 2)

    def format_buffer(self, value: str) -> str:
        if not value or value == "-":
            return self.format_number(0.0)
        if value.endswith(self._dec):
            return value
        try:
            return self.format_number(float(value.replace(self._dec, ".")))
        except ValueError:
            return self.format_number(0.0)

    def _pending_display_text(self) -> str:
        return self.format_buffer(self.cpu.pending_token().replace(".", self._dec))

    def _refresh_lcd(self):
        self.lcd_display.setPlainText(self.format_buffer(self.cpu.get_tempinput()))

    # entradas
    def enter_argument(self, x):
        self.cpu.buffer_append(x)
        self._refresh_lcd()
        self.update_status_bar()

    def update_rollertape(self, txt: str):
        cursor = self.gui_rollertape.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(txt + '\n')
        self.gui_rollertape.setTextCursor(cursor)
        self.gui_rollertape.ensureCursorVisible()

    def update_status_bar(self):
        mem = f"M: {self.format_number(self.cpu.memory)}" if self.cpu.memory else "M: —"
        total = self.format_number(self.cpu.running_total())
        self.status_bar.showMessage(f"{mem} | Total: {total}")

    # acciones
    def clear(self, _=None):
        self.cpu.reset()
        self.lcd_display.setPlainText(self.format_number(0.0))
        self.gui_rollertape.clear()
        self.update_status_bar()

    def clear_entry(self, _=None):
        self.cpu.buffer_reset()
        self.lcd_display.setPlainText(self.format_number(0.0))
        self.update_status_bar()

    def clear_tape(self, _=None):
        self.gui_rollertape.clear()
        self.update_status_bar()

    def _operator_pressed(self, symbol, label):
        txt = self._pending_display_text()
        getattr(self.cpu, {"+": "add", "-": "sub", "*": "mul", "/": "div"}[symbol])()
        self.update_rollertape(txt + f" {label}")
        self._refresh_lcd()
        self.update_status_bar()

    def add(self, _=None): self._operator_pressed("+", "+")
    def sub(self, _=None): self._operator_pressed("-", "-")
    def mul(self, _=None): self._operator_pressed("*", "×")
    def div(self, _=None): self._operator_pressed("/", "÷")

    def evaluate(self, _=None):
        operand = self._pending_display_text()
        self.update_rollertape(operand + " =")
        try:
            value = self.cpu.evaluate()
        except Exception:
            self.update_rollertape("Error")
            self.lcd_display.setPlainText("Error")
            self.update_status_bar()
            return
        self.update_rollertape("~~~~~~~~~~~~~~~~~~~~~~~~")
        self.update_rollertape(self.format_number(value))
        self.update_rollertape("")
        self.lcd_display.setPlainText(self.format_number(value))
        self.update_status_bar()

    def memory_clear(self, _=None): self.cpu.memory_clear(); self.update_status_bar()
    def memory_recall(self, _=None):
        self.cpu.memory_recall()
        self._refresh_lcd()
        self.update_status_bar()
    def memory_store(self, _=None): self.cpu.memory_store(); self.update_status_bar()
    def memory_add(self, _=None): self.cpu.memory_add(); self.update_status_bar()

    def back(self, _=None):
        self.cpu.buffer_remove()
        self._refresh_lcd()
        self.update_status_bar()

    def negate(self, _=None):
        self.cpu.negate()
        self._refresh_lcd()
        self.update_status_bar()

    # teclado
    def keyPressEvent(self, event):
        key, mods = event.key(), event.modifiers()
        if mods & Qt.ControlModifier:
            ctrl_map = {
                Qt.Key_M: self.memory_store,
                Qt.Key_R: self.memory_recall,
                Qt.Key_L: self.memory_clear,
                Qt.Key_P: self.memory_add,
            }
            handler = ctrl_map.get(key)
            if handler:
                handler()
                return
        if Qt.Key_0 <= key <= Qt.Key_9:
            self.enter_argument(str(key - Qt.Key_0))
        elif key == Qt.Key_Plus:
            self.add()
        elif key == Qt.Key_Minus:
            self.sub()
        elif key == Qt.Key_Asterisk:
            self.mul()
        elif key == Qt.Key_Slash:
            self.div()
        elif key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Equal):
            self.evaluate()
        elif key in (Qt.Key_Period, Qt.Key_Comma):
            self.enter_argument(self._dec)
        elif key == Qt.Key_Backspace:
            self.back()
        elif key == Qt.Key_Escape:
            self.clear()
        elif key == Qt.Key_Delete:
            self.clear_entry()

    def copy_to_clipboard(self):
        text = self.cpu.get_tempinput() or self._pending_display_text()
        QApplication.clipboard().setText(text)

    def paste_from_clipboard(self):
        txt = QApplication.clipboard().text()
        if txt:
            self.cpu.buffer_append(txt)
            self._refresh_lcd()
            self.update_status_bar()

    def show_about_dialog(self):
        QMessageBox.about(
            self, "About",
            f"GNU Roll Tape Calc\nVersion {_VERSION}\nDeveloped by Pablo Niklas"
        )


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.main_view = CalcFrame()
        self.main_view.show()


def main():
    if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = App(sys.argv)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
