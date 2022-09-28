import tkinter as tk
from tkinter import ttk, NORMAL, DISABLED
import tkinter.font as font


class CalcFrame(ttk.Frame):

    def __init__(self, gui_container):
        super().__init__(gui_container)

        self.gui_container = gui_container

        self.cpu = Cpu()

        # TODO: Calcular row y col con font_size del parent.
        self._rollertape_max_col = 25
        self._rollertape_max_row = 12

        for i in range(0, self._rollertape_max_row + 4):
            self.gui_container.rowconfigure(i, weight=1)

        for i in range(0, 6):
            self.gui_container.columnconfigure(i, weight=1)

        # add padding to the frame and show it
        #self.gui_container.grid(padx=10, pady=10, sticky=tk.NSEW)

        self.buttons = []
        self.columns = 4

        self._reset_rollertape()

        self._rollertape_font_size = 15

        self._rollertape_font = font.Font(family="Roboto Mono",
                                          size=self._rollertape_font_size
                                          )

        self._key_font = font.Font(family="Roboto Mono",
                                   size=20
                                   )

        self.gui_rollertape = tk.Text(self.gui_container,
                                      width=self._rollertape_max_col,
                                      height=self._rollertape_max_row,
                                      background="white",
                                      font=self._rollertape_font
                                      )

        # Init calc.
        self.create_widgets()
        self.update_rollertape("Ready.")
        self.update_rollertape("0.")
        self.gui_container.focus_set()

    def create_widgets(self):
        padx, pady = 5, 5
        num_buttons = 11

        self.gui_rollertape.grid(rowspan=4, row=1, column=4)

        self.gui_container.gui_buttons = [tk.Button(self)] * num_buttons

        # Keyboard events
        for i in range(0, num_buttons):
            self.gui_container.bind(str(i), lambda event: self.enter_argument(i))
            self.gui_container.gui_buttons[i] = tk.Button(self.gui_container,
                                                          text=str(i),
                                                          width=5,
                                                          height=5,
                                                          font=self._key_font,
                                                          command=f"self.enter_argument({i})")

        self.gui_container.gui_buttons[10] = tk.Button(self.gui_container,
                                                      text=".",
                                                      width=5,
                                                      height=5,
                                                      font=self._key_font,
                                                      command=f"self.enter_argument({i})")


        # Position the buttons in the grid.
        self.gui_container.gui_buttons[0].grid(column=1, row=4, padx=padx, pady=pady)

        self.gui_container.gui_buttons[1].grid(column=1, row=3, padx=padx, pady=pady)
        self.gui_container.gui_buttons[2].grid(column=2, row=3, padx=padx, pady=pady)
        self.gui_container.gui_buttons[3].grid(column=3, row=3, padx=padx, pady=pady)

        self.gui_container.gui_buttons[4].grid(column=1, row=2, padx=padx, pady=pady)
        self.gui_container.gui_buttons[5].grid(column=2, row=2, padx=padx, pady=pady)
        self.gui_container.gui_buttons[6].grid(column=3, row=2, padx=padx, pady=pady)

        self.gui_container.gui_buttons[7].grid(column=1, row=1, padx=padx, pady=pady)
        self.gui_container.gui_buttons[8].grid(column=2, row=1, padx=padx, pady=pady)
        self.gui_container.gui_buttons[9].grid(column=3, row=1, padx=padx, pady=pady)

        self.gui_container.gui_buttons[10].grid(column=2, row=4, padx=padx, pady=pady)


        self.gui_container.bind("q", lambda event: self.gui_container.destroy())
        self.gui_container.bind("Q", lambda event: self.gui_container.destroy())

    def enter_argument(self, x: int):
        self.gui_container.gui_buttons[x].configure(background="red")
        self.cpu.buffer_append(x)
        self.gui_container.gui_buttons[x].configure(background="white")

    def update_rollertape(self, txt: str):
        self.rollertape_buffer = self.rollertape_buffer[1:]  # Scroll
        self.rollertape_buffer.append(txt)

        line = ''.join(x.rjust(self._rollertape_max_col + 2, " ") +
                       "\n" for x in self.rollertape_buffer)

        self.gui_rollertape.config(state=NORMAL)
        self.gui_rollertape.insert('1.0', line)
        self.gui_rollertape.config(state=DISABLED)

    def _reset_rollertape(self):
        self.rollertape_buffer = [""] * self._rollertape_max_row


class Cpu:

    def __init__(self):
        self._tempinput = ""
        self._operation = []
        self._total = 0


    def buffer_append(self, x: int):
        self._tempinput += str(x)

    def buffer_remove(self):
        if len(self._tempinput) > 1:
            self._tempinput = self._tempinput[:-1]
        elif self._tempinput != "0":
            self._tempinput = 0

    def add(self):
        self._operation.append(self._tempinput)
        self._operation.append("+")


    def sub(self):
        pass

    def div(self):
        pass

    def mul(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # self.resizable(width=False, height=False)
        self.configure(background="grey")
        self.geometry('400x250')
        self.title("Calculadora")


if __name__ == "__main__":
    app = App()
    CalcFrame(app)
    app.mainloop()
