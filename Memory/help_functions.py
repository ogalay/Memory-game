import tkinter as tk
from pathlib import Path
from os.path import dirname, join

TEXT_FOLDER = join(Path(dirname(__file__)).parent, 'text_files')


def print_rules() -> None:

    rule_window = tk.Toplevel()
    rule_window.resizable(False, False)
    rule_window.title("How to play?")
    with open(f'{TEXT_FOLDER}/rules_eng.txt') as f:
        game_rules = f.read()
    lab_rule = tk.Label(rule_window, text=game_rules,
                        fg="black", anchor="e", justify=tk.LEFT)
    lab_rule.pack(side=tk.TOP)
    rule_window.mainloop()

