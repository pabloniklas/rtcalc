import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QTextEdit, QLCDNumber
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QLocale, QTimer

class CalcFrame(QWidget):
    def __init__(self):
        super().__init__()

        self.cpu = Cpu()
        self._rollertape_max_col = 25
        self._rollertape_max_row = 12

        self._rollertape_font_size = 15
        self._rollertape_font = QFont("Roboto Mono", self._rollertape_font_size)
        self._key_font = QFont("Roboto Mono", 20)

        self.initUI()

    def initUI(self):
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        self.gui_rollertape = QTextEdit()
        self.gui_rollertape.setFont(self._rollertape_font)
        self.gui_rollertape.setReadOnly(True)
        vbox.addWidget(self.gui_rollertape)

        self.lcd_display = QLCDNumber()
        self.lcd_display.setDigitCount(10)
        self.lcd_display.setSegmentStyle(QLCDNumber.Flat)
        self.lcd_display.setPalette(self.createPalette())
        self.lcd_display.setStyleSheet("background: rgb(255, 228, 181); color: black; border: 1px solid black;")
        self.lcd_display.setMode(QLCDNumber.Dec)
        self.lcd_display.setSmallDecimalPoint(True)
        vbox.addWidget(self.lcd_display)

        self.buttons = []
        grid = QGridLayout()
        vbox.addLayout(grid)

        self.gui_buttons = []

        # Create number buttons
        for i in range(10):
            button = QPushButton(str(i))
            button.setFont(self._key_font)
            button.clicked.connect(lambda _, x=i: self.enter_argument(str(x)))
            self.gui_buttons.append(button)

        # Create decimal button
        decimal_separator = QLocale.system().decimalPoint()
        button = QPushButton(decimal_separator)
        button.setFont(self._key_font)
        button.clicked.connect(lambda: self.enter_argument(decimal_separator))
        self.gui_buttons.append(button)

        # Create clear button
        button = QPushButton("C")
        button.setFont(self._key_font)
        button.clicked.connect(self.clear)
        self.gui_buttons.append(button)

        # Position number buttons in the grid
        positions = [(4, 1), (3, 1), (3, 2), (3, 3), (2, 1), (2, 2), (2, 3), (1, 1), (1, 2), (1, 3), (4, 2), (4, 4)]
        for i, (row, col) in enumerate(positions):
            grid.addWidget(self.gui_buttons[i], row, col)

        # Create operation buttons
        operations = [('+', self.add), ('-', self.sub), ('*', self.mul), ('/', self.div), ('=', self.evaluate)]
        self.op_buttons = []
        for i, (text, command) in enumerate(operations):
            button = QPushButton(text)
            button.setFont(self._key_font)
            button.clicked.connect(command)
            grid.addWidget(button, i + 1, 4)
            self.op_buttons.append(button)

        self.update_rollertape("Ready.")
        self.update_rollertape("0.")

    def createPalette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 228, 181))  # Ocre claro
        palette.setColor(QPalette.WindowText, Qt.black)  # Texto negro
        return palette

    def enter_argument(self, x):
        # Handle decimal point
        if x == QLocale.system().decimalPoint():
            if QLocale.system().decimalPoint() not in self.cpu.get_tempinput():
                self.cpu.buffer_append(x)
        else:
            self.cpu.buffer_append(x)

        self.lcd_display.display(self.format_display(self.cpu.get_tempinput()))

    def format_display(self, value):
        try:
            # Ensure the number is a float and format it with 2 decimal places
            number = float(value.replace(QLocale.system().decimalPoint(), '.'))
            formatted_value = f"{number:.2f}"
            # Replace the decimal point with the system locale's decimal point
            return formatted_value.replace('.', QLocale.system().decimalPoint())
        except ValueError:
            return "0"

    def update_rollertape(self, txt: str):
        # Clean the previous content and add the new content
        self.gui_rollertape.append(txt)

    def clear(self):
        self.cpu.reset()
        self.lcd_display.display("0")
        self.update_rollertape("0.")

    def add(self):
        self.cpu.add()
        self.update_rollertape(self.cpu.get_operation()[-2] + self.cpu.get_operation()[-1])
        self.lcd_display.display("0")

    def sub(self):
        self.cpu.sub()
        self.update_rollertape(self.cpu.get_operation()[-2] + self.cpu.get_operation()[-1])
        self.lcd_display.display("0")

    def mul(self):
        self.cpu.mul()
        self.update_rollertape(self.cpu.get_operation()[-2] + self.cpu.get_operation()[-1])
        self.lcd_display.display("0")

    def div(self):
        self.cpu.div()
        self.update_rollertape(self.cpu.get_operation()[-2] + self.cpu.get_operation()[-1])
        self.lcd_display.display("0")

    def evaluate(self):
        result = self.cpu.evaluate()
        self.lcd_display.display(result)
        self.update_rollertape("=" + result)

    def keyPressEvent(self, event):
        key = event.key()
        if Qt.Key_0 <= key <= Qt.Key_9:
            self.enter_argument(str(key - Qt.Key_0))
            self.highlight_button(self.gui_buttons[key - Qt.Key_0])
        elif key == Qt.Key_Plus:
            self.add()
            self.highlight_button(self.op_buttons[0])
        elif key == Qt.Key_Minus:
            self.sub()
            self.highlight_button(self.op_buttons[1])
        elif key == Qt.Key_Asterisk:
            self.mul()
            self.highlight_button(self.op_buttons[2])
        elif key == Qt.Key_Slash:
            self.div()
            self.highlight_button(self.op_buttons[3])
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            self.evaluate()
            self.highlight_button(self.op_buttons[4])
        elif key == Qt.Key_C:
            self.clear()
            self.highlight_button(self.gui_buttons[11])
        elif key == Qt.Key_Backspace:
            self.cpu.buffer_remove()
            self.lcd_display.display(self.format_display(self.cpu.get_tempinput()))
        elif key == Qt.Key_Period:
            self.enter_argument(QLocale.system().decimalPoint())
            self.highlight_button(self.gui_buttons[10])

    def highlight_button(self, button):
        button.setStyleSheet("background-color: lightblue")
        QTimer.singleShot(150, lambda: button.setStyleSheet(""))

class Cpu:

    def __init__(self):
        self._tempinput = ""
        self._operation = []
        self._total = 0

    def buffer_append(self, x):
        if x == QLocale.system().decimalPoint() and QLocale.system().decimalPoint() in self._tempinput:
            return
        self._tempinput += str(x)

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

    def get_operation(self):
        return self._operation

    def evaluate(self):
        self._operation.append(self._tempinput)
        expression = "".join(self._operation)
        try:
            self._total = eval(expression)
            result = "{:.2f}".format(self._total)
            self._operation = [result]
            self._tempinput = ""
            return result
        except Exception as e:
            self.reset()
            return "Error"

class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = CalcFrame()
        self.window.setWindowTitle("Calculadora")
        self.window.resize(400, 400)
        self.window.show()

if __name__ == "__main__":
    app = App(sys.argv)
    sys.exit(app.exec_())
