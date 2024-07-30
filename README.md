# Calculator with PyQt5

This project is a simple calculator developed in Python using PyQt5. The application includes an LCD screen that displays numbers and results, a "roller tape" to record operations and results, and a numeric keypad with buttons for basic operations.

## Features

- **User Interface**:
  - LCD screen that displays numbers with a light ochre background and black text.
  - Roller tape that shows performed operations and results.
  - Numeric keypad with buttons for digits, operations, and special functions.

- **Functions**:
  - Input of numbers and operations.
  - Performing basic mathematical operations: addition, subtraction, multiplication, and division.
  - Evaluation and display of the result.
  - Support for the decimal point according to the operating system's regional settings.
  - Correction of entries with the Backspace button.
  - Reset with the "C" button.

- **Keyboard Event Support**:
  - The buttons on the numeric keypad and for operations respond to corresponding keyboard events.

## Installation

To run this project, make sure you have Python 3, PyQt5, and qtawesome installed in your environment. You can install PyQt5 using `pip`:

```bash
pip install PyQt5 qtawesome
```

## Generating a standalone executable

To generate the executable:

```bash
pyinstaller --onefile --add-data "font/MPLUS1Code-Regular.ttf:." rollcalc.py
```

