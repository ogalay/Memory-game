import tkinter as tk
from Memory.help_functions import print_rules
from Memory.game import Game


def launch_game() -> None:
    # GUI
    window = tk.Tk()

    window.title("Memory game")

    memory_game = Game(window)
    top = tk.Menu(window)
    window.config(menu=top)

    top.add_command(label='Close', command=window.destroy)
    top.add_command(label='How to play?', command=print_rules)

    # Launch GUI
    window.mainloop()
