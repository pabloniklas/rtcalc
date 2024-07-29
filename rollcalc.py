import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QTextEdit, QHBoxLayout, QSizePolicy, QStatusBar, QMenuBar, QAction, QMessageBox
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor, QIcon
from PyQt5.QtCore import Qt, QLocale

import locale

import qtawesome as qta

class CalcFrame(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu = Cpu()
        self._rollertape_max_col = 25
        self._rollertape_max_row = 12

        self._rollertape_font_size = 15
        self._rollertape_font = QFont("Courier", self._rollertape_font_size)
        self._key_font = QFont("Roboto Condensed", 15)

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create menu bar
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("QMenuBar { font-size: 12pt; } QMenu { font-size: 12pt; }")
        main_layout.setMenuBar(menu_bar)

        # Create File menu
        file_menu = menu_bar.addMenu("File")
        exit_action = QAction(QIcon.fromTheme('application-exit'), "Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Create Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction(QIcon.fromTheme('edit-copy'), "Copy", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        paste_action = QAction(QIcon.fromTheme('edit-paste'), "Paste", self)
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        # Create About menu
        about_menu = menu_bar.addMenu("About")
        about_action = QAction(QIcon.fromTheme('help-about'), "About", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_menu.addAction(about_action)

        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        left_layout = QVBoxLayout()
        top_layout.addLayout(left_layout)

        # Reemplazar el panel LCD por un panel de texto de solo lectura
        self.lcd_display = QTextEdit()
        self.lcd_display.setFont(self._rollertape_font)
        self.lcd_display.setReadOnly(True)
        self.lcd_display.setAlignment(Qt.AlignRight)  # Justificación a la derecha
        self.lcd_display.setFixedHeight(40)
        self.lcd_display.setStyleSheet("background: rgb(255, 228, 181); color: black; border: 1px solid black;")
        left_layout.addWidget(self.lcd_display)

        self.buttons = []
        grid = QGridLayout()
        left_layout.addLayout(grid)

        self.gui_buttons = []

        # Create buttons
        buttons = [
            ('Back', self.back), ('CE', self.clear_entry), ('C', self.clear), ('CT', self.clear_tape),
            ('MC', self.memory_clear), ('7', self.enter_argument), ('8', self.enter_argument), ('9', self.enter_argument), ('/', self.div),
            ('MR', self.memory_recall), ('4', self.enter_argument), ('5', self.enter_argument), ('6', self.enter_argument), ('*', self.mul),
            ('MS', self.memory_store), ('1', self.enter_argument), ('2', self.enter_argument), ('3', self.enter_argument), ('-', self.sub),
            ('M+', self.memory_add), ('0', self.enter_argument), ('000', self.enter_argument), ('.', self.enter_argument), ('+', self.add)
        ]

        positions = [(i, j) for i in range(6) for j in range(5)]
        for position, (text, method) in zip(positions, buttons):
            button = QPushButton(text)
            button.setFont(self._key_font)

            if text == "Back":
                button.setStyleSheet("background-color: #f04a50; border: 1px solid gray;")
                button.setText("\u232B")
            else:
                button.setStyleSheet("background-color: lightgray; border: 1px solid gray;")

            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            button.clicked.connect(lambda _, x=text: method(x))
            grid.addWidget(button, *position)
            self.gui_buttons.append(button)

        # Add "=" button spanning across the entire width of the button panel
        equal_button = QPushButton('=')
        equal_button.setFont(self._key_font)
        equal_button.setStyleSheet("background-color: #6db442; border: 1px solid gray; color: white;")
        equal_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        equal_button.clicked.connect(self.evaluate)
        grid.addWidget(equal_button, 6, 0, 1, 5)
        self.gui_buttons.append(equal_button)

        for i in range(grid.rowCount()):
            for j in range(grid.columnCount()):
                grid.setRowStretch(i, 1)
                grid.setColumnStretch(j, 1)

        # Create roller tape
        self.gui_rollertape = QTextEdit()
        self.gui_rollertape.setFont(self._rollertape_font)
        self.gui_rollertape.setReadOnly(True)
        self.gui_rollertape.setAlignment(Qt.AlignRight)  # Justificación a la derecha
        top_layout.addWidget(self.gui_rollertape)

        # Create status bar
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        self.update_status_bar()

    def createPalette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 228, 181))  # Ocre claro
        palette.setColor(QPalette.WindowText, Qt.black)  # Texto negro
        return palette

    def enter_argument(self, x):
        if x == QLocale.system().decimalPoint():
            if QLocale.system().decimalPoint() not in self.cpu.get_tempinput():
                self.cpu.buffer_append(x)
        else:
            self.cpu.buffer_append(x)
        self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))
        self.update_status_bar()

    def format_display(self, value):
        # Obtener la configuración regional actual del sistema operativo
        locale.setlocale(locale.LC_ALL, '')

        try:
            number = float(value.replace(QLocale.system().decimalPoint(), '.'))

            # Redondear el número a dos decimales
            numero_redondeado = round(number, 2)

            # Formatear el número de acuerdo con la configuración regional
            numero_formateado = locale.format_string("%.2f", numero_redondeado, grouping=True)

            return numero_formateado
        except ValueError:
            return "0.00"

    def update_rollertape(self, txt: str):
        cursor = self.gui_rollertape.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(txt + '\n')
        self.gui_rollertape.setTextCursor(cursor)
        self.gui_rollertape.ensureCursorVisible()
        self.update_status_bar()

    def update_status_bar(self):
        numlock_status = "NumLock On" if self.is_numlock_active() else "NumLock Off"
        buffer_sum = sum(float(op.replace(QLocale.system().decimalPoint(), ".")) for op in self.cpu._operation if op.replace(QLocale.system().decimalPoint(), "").replace(".", "").isdigit())
        buffer_sum_str = f"Buffer Total: {buffer_sum:.2f}".replace(".", QLocale.system().decimalPoint())
        self.status_bar.showMessage(f"{numlock_status} | {buffer_sum_str}")

    def is_numlock_active(self):
        return QApplication.queryKeyboardModifiers() & Qt.KeypadModifier

    def clear(self, x=None):
        self.cpu.reset()
        self.lcd_display.setPlainText("0.00")
        self.gui_rollertape.clear()  # Clear the roller tape
        self.update_rollertape("0.00")
        self.update_status_bar()

    def clear_entry(self, x=None):
        self.cpu.buffer_reset()
        self.lcd_display.setPlainText("0.00")
        self.update_status_bar()

    def clear_tape(self, x=None):
        self.gui_rollertape.clear()
        self.update_status_bar()

    def add(self, x=None):
        self.cpu.add()
        self.update_rollertape(self.format_display(self.cpu.get_tempinput()) + " +")
        self.cpu.buffer_reset()
        self.update_status_bar()

    def sub(self, x=None):
        self.cpu.sub()
        self.update_rollertape(self.format_display(self.cpu.get_tempinput()) + " -")
        self.cpu.buffer_reset()
        self.update_status_bar()

    def mul(self, x=None):
        self.cpu.mul()
        self.update_rollertape(self.format_display(self.cpu.get_tempinput()) + " *")
        self.cpu.buffer_reset()
        self.update_status_bar()

    def div(self, x=None):
        self.cpu.div()
        self.update_rollertape(self.format_display(self.cpu.get_tempinput()) + " /")
        self.cpu.buffer_reset()
        self.update_status_bar()

    def evaluate(self, x=None):
        self.cpu._operation.append(self.cpu.get_tempinput())  # Añadir el último operando antes de evaluar
        self.update_rollertape(self.format_display(self.cpu.get_tempinput()) + " +")  # Mostrar la operación completa
        self.update_rollertape("--------------------")
        result = self.cpu.evaluate()
        self.update_rollertape(self.format_display(result))
        self.update_rollertape("")
        self.lcd_display.setPlainText(self.format_display(result))
        self.cpu.buffer_reset()
        self.update_status_bar()

    def memory_clear(self, x=None):
        self.cpu.memory_clear()
        self.update_status_bar()

    def memory_recall(self, x=None):
        self.cpu.memory_recall()
        self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))
        self.update_status_bar()

    def memory_store(self, x=None):
        self.cpu.memory_store()
        self.update_status_bar()

    def memory_add(self, x=None):
        self.cpu.memory_add()
        self.update_status_bar()

    def back(self, x=None):
        self.cpu.buffer_remove()
        self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))
        self.update_status_bar()

    def negate(self, x=None):
        self.cpu.negate()
        self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))
        self.update_status_bar()

    def keyPressEvent(self, event):
        key = event.key()
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
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            self.evaluate()
        elif key == Qt.Key_Period:
            self.enter_argument(QLocale.system().decimalPoint())
        elif key == Qt.Key_Backspace:
            self.cpu.buffer_remove()
            self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))
        elif key == Qt.Key_Comma:
            self.enter_argument(QLocale.system().decimalPoint())

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.cpu.get_tempinput())

    def paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        self.cpu.buffer_append(clipboard.text())
        self.lcd_display.setPlainText(self.format_display(self.cpu.get_tempinput()))

    def show_about_dialog(self):
        QMessageBox.about(self, "About", "GNU Roll Tape Calc\nVersion 1.0\nDeveloped by Pablo Niklas")


class Cpu:
    def __init__(self):
        self._tempinput = ""
        self._operation = []
        self.memory = 0

    def buffer_append(self, x):
        if x == QLocale.system().decimalPoint() and QLocale.system().decimalPoint() in self._tempinput:
            return
        self._tempinput += str(x)

    def buffer_reset(self):
        self._tempinput = ""

    def buffer_remove(self):
        if len(self._tempinput) > 1:
            self._tempinput = self._tempinput[:-1]
        else:
            self._tempinput = "0"

    def add(self):
        self._operation.append(self._tempinput)
        self._operation.append("+")

    def sub(self):
        self._operation.append(self._tempinput)
        self._operation.append("-")

    def div(self):
        self._operation.append(self._tempinput)
        self._operation.append("/")

    def mul(self):
        self._operation.append(self._tempinput)
        self._operation.append("*")

    def reset(self):
        self._tempinput = ""
        self._operation = []

    def get_tempinput(self):
        return self._tempinput

    def get_operation_string(self):
        return ' '.join(self._operation)

    def evaluate(self):
        self._operation.append(self._tempinput)
        try:
            expression = ''.join(self._operation[:-1]).replace(QLocale.system().decimalPoint(), ".")

            result = str(round(eval(expression), 2))
            result = result.replace('.', QLocale.system().decimalPoint())
            self.reset()
            return result
        except Exception as e:
            return "Error"

    def memory_clear(self):
        self.memory = 0

    def memory_recall(self):
        self._tempinput = str(self.memory)

    def memory_store(self):
        try:
            self.memory = float(self._tempinput.replace(QLocale.system().decimalPoint(), "."))
        except ValueError:
            self.memory = 0

    def memory_add(self):
        try:
            self.memory += float(self._tempinput.replace(QLocale.system().decimalPoint(), "."))
        except ValueError:
            pass

    def negate(self):
        if self._tempinput.startswith("-"):
            self._tempinput = self._tempinput[1:]
        else:
            self._tempinput = "-" + self._tempinput


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.main_view = CalcFrame()
        self.main_view.setWindowTitle('GNU Roll Tape Calc')
        self.main_view.resize(800, 400)

        # Establecer tamaño fijo para la ventana
        self.main_view.setFixedSize(800, 400)

        self.main_view.show()


if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
