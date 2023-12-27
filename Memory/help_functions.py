"""Define help functions for GUI menu."""

import tkinter as tk
from pathlib import Path
from os.path import dirname, join

TEXT_FOLDER = join(Path(dirname(__file__)).parent, 'text_files')


def print_rules() -> None:
    """
    Display rules and gameplay.

    Load a text files 'rules_eng.txt'.
    Open a second window.
    Write the content of the text document.
    Returns
    -------
    None.
    """
    rule_window = tk.Toplevel()
    rule_window.resizable(False, False)
    rule_window.title("How to play?")
    with open(f'{TEXT_FOLDER}/rules_eng.txt') as f:
        gameRules = f.read()
    lab_Rule = tk.Label(rule_window, text=gameRules,
                        fg="black", anchor="e", justify=tk.LEFT)
    lab_Rule.pack(side=tk.TOP)
    rule_window.mainloop()
