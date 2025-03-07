from Memory.player import Player
from random import choice, sample
import tkinter as tk
from typing import List
from pathlib import Path
from os.path import dirname, join, isdir
from os import listdir
import pandas as pd
import mne
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import io
import time
import argparse
import numpy as np
from brainflow.board_shim import BoardShim, BrainFlowInputParams

IMAGES_FOLDER = join(Path(dirname(__file__)).parent, 'Images')
DATA_FOLDER = join(Path(dirname(__file__)).parent, 'eeg_data')


def find_all_themes():
    all_themes = [theme for theme in listdir(IMAGES_FOLDER)
                  if isdir(join(IMAGES_FOLDER, theme))]
    all_themes.sort()
    return all_themes

class Game:

    def __init__(self, window):
        self.THEMES = find_all_themes()
        self.THEME_CARDS = self.generate_theme_cards_list()
        self.player = Player()
        # self.player2 = None
        # self.current_player = self.player1
        self.player_nb = 1
        self.game_mode = 0
        self.game_num = 0
        # self.set_one_player_mode()
        self.game_over = False
        self.image = None

        self.DIMENSIONS = [(5, 4), (6, 6)]
        self.game_dim = self.DIMENSIONS[0]
        self.cards_nb = self.game_dim[0] * self.game_dim[1]

        self.theme = self.THEMES[0]

        self.hidden_card = tk.PhotoImage(
            file=f'{IMAGES_FOLDER}/{self.theme}/carte-0.gif'
        )
        self.blank_card = tk.PhotoImage(
            file=f'{IMAGES_FOLDER}/{self.theme}/blankCard.gif'
        )
        self.turned_cards_nb = 0  # Number of visible cards
        self.turned_cards_ids = []  # List of index of turned over cards
        self.turned_card_played = []  # List of index of played cards
        self.found_cards = []  # List of index of found pairs
        self.cards_ids = []  # List of index of cards

        self.window = window
        self.radio_button_choice = tk.IntVar()
        self.set_radio_buttons()
        self.main_frame = tk.Frame(self.window, height=500, width=500)
        self.cards_frame = tk.Frame(self.window)
        self.parser = None
        self.args = None
        self.params = None
        self.openbci = None
        self.record_short = None
        self.record_long = None
        # self.set_up_theme_frame()

    def generate_theme_cards_list(self):
        return [tk.PhotoImage(file=str(f'{IMAGES_FOLDER}/{theme}/carte-0.gif'))
                for theme in self.THEMES]

    def set_initial_game_parameters(self):
        x = self.radio_button_choice.get()
        self.game_mode = x
        #buf = self.draw_demo_plot()
        #self.open_game_over_frame(buf)
        if self.game_mode == 1:
            self.parser = argparse.ArgumentParser()
            self.parser.add_argument('--serial-port', type=str,
                                help='serial port', required=False, default='COM4')
            self.parser.add_argument('--board-id', type=int,
                                help='board id', required=False, default=0)
            self.args = self.parser.parse_args()
            self.params = BrainFlowInputParams()
            self.params.serial_port = self.args.serial_port
            self.openbci = BoardShim(self.args.board_id, self.params)

        self.start_new_game()

    def set_radio_buttons(self):
        self.radio_buttons_frame = tk.Frame(self.window, height=500, width=500)
        self.radio_buttons_frame.grid(row=0, column=5)

        self.hello = tk.Label(
            self.radio_buttons_frame,
            text='Choose the game mode:',
            font=("Helvetica", 14),
            width=25
        )
        self.hello.grid(row=0, column=0, sticky=tk.W)

        self.R1 = tk.Radiobutton(
            self.radio_buttons_frame,
            text="Demo mode",
            font=("Helvetica", 14),
            command=self.set_initial_game_parameters,
            variable=self.radio_button_choice,
            value=0,
            width=25
        )
        self.R1.grid(row=1, column=0, sticky=tk.W)

        self.R2 = tk.Radiobutton(
            self.radio_buttons_frame,
            text="Real mode",
            font=("Helvetica", 14),
            command=self.set_initial_game_parameters,
            variable=self.radio_button_choice,
            value=1,
            width=25
        )
        self.R2.grid(row=2, column=0, sticky=tk.W)

    def set_game_over(self):
        if len(self.found_cards) == self.cards_nb:
            if self.game_num == 0:
                self.game_num = 1
                self.game_dim = self.DIMENSIONS[1]
                self.cards_nb = self.game_dim[0] * self.game_dim[1]
                self.theme = self.THEMES[1]
                self.hidden_card = tk.PhotoImage(
                    file=f'{IMAGES_FOLDER}/{self.theme}/carte-0.gif'
                )
                self.blank_card = tk.PhotoImage(
                    file=f'{IMAGES_FOLDER}/{self.theme}/blankCard.gif'
                )
                if self.game_mode == 1:
                    self.record_short = self.openbci.get_board_data()
                    self.openbci.stop_stream()
                    self.openbci.release_session()
                self.window.after(3000, self.start_new_game())
            else:
                self.game_over = True
                if self.game_mode == 0:
                    fig = self.draw_demo_plot()
                    self.window.after(2000, self.open_game_over_frame(fig))
                else:
                    self.record_long = self.openbci.get_board_data()
                    self.openbci.stop_stream()
                    self.openbci.release_session()
                    fig = self.draw_real_plot()
                    self.window.after(5000, self.open_game_over_frame(fig))

    def draw_plot(self, rec1, rec2, info):
        raw1 = mne.io.RawArray(rec1, info)
        raw2 = mne.io.RawArray(rec2, info)

        raw1 = raw1.filter(1, 45, fir_design='firwin', skip_by_annotation='edge')
        raw2 = raw2.filter(1, 45, fir_design='firwin', skip_by_annotation='edge')

        events1 = mne.make_fixed_length_events(raw1, duration=2.0)
        events2 = mne.make_fixed_length_events(raw2, duration=2.0)

        epochs1 = mne.Epochs(raw1, events1, tmin=-0.2, tmax=0.5, preload=True)
        epochs2 = mne.Epochs(raw2, events2, tmin=-0.2, tmax=0.5, preload=True)

        evoked1 = epochs1.average()
        evoked2 = epochs2.average()

        plot = mne.viz.plot_compare_evokeds(dict(short=evoked1, long=evoked2), legend='upper right', show=True)
        fig = plt.figure(plot[0])

        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)

        return buf

    def draw_demo_plot(self):
        ch_names = ['Fp1', 'Fp2', 'Fpz', 'AF7', 'AF3', 'AF4',
                    'AF8', 'F7']
        sfreq = 250.0
        ch_types = ['eeg'] * 8
        info = mne.create_info(ch_names, sfreq, ch_types)

        rec1 = pd.read_csv('eeg_data/state_1_day_4.csv', delimiter=',', header=None)
        rec2 = pd.read_csv('eeg_data/state_2_day_4.csv', delimiter=',', header=None)

        fig = self.draw_plot(rec1, rec2, info)

        return fig

        #plt.savefig('eeg_data/demo_plot.png')
        #pre, ext = os.path.splitext('eeg_data/demo_plot.png')
        #os.rename('eeg_data/demo_plot.png', pre + '.gif')

    def draw_real_plot(self):
        ch_names = ['F7', 'C4', 'F8', 'O2', 'O1', 'C3']
        sfreq = 250.0
        ch_types = ['eeg'] * len(ch_names)
        info = mne.create_info(ch_names, sfreq, ch_types)

        rec1 = self.record_short[[2, 3, 4, 6, 7, 8]]
        print(rec1)
        rec2 = self.record_long[[2, 3, 4, 6, 7, 8]]

        fig = self.draw_plot(rec1, rec2, info)
        print('Trying to do plot')

        return fig

    def open_game_over_frame(self, fig):
        # game_over_window = tk.Toplevel(self.window)
        # game_over_window.title("Game Over")
        # game_over_window.geometry("900x700")

        self.main_frame.destroy()
        self.cards_frame.destroy()
        self.radio_buttons_frame.destroy()
        self.main_frame = tk.Frame(self.window, width=900, height=700)
        self.main_frame.grid(row=0, column=1)

        tk.Label(
            master=self.main_frame,
            text='Your epochs difference:',
            font=("Helvetica", 20)
        ).grid(row=0, column=0)


        self.image = ImageTk.PhotoImage(Image.open(fig))
        tk.Label(
            master=self.main_frame,
            image=self.image
        ).grid(row=1, column=0)

    # def reset_scores(self) -> None:
    #
    #    self.player1.reset_score()

    # for player in (self.player1, self.player2):
    #    try:
    #        player.reset_score()
    #    except AttributeError:
    #        pass

    def reset_game(self):
        self.player.reset_score()
        self.turned_cards_nb = 0
        self.found_cards = []
        self.turned_cards_ids = []
        self.turned_card_played = []
        self.game_over = False

    def find_total_nb_cards_theme(self):
        return len([file for file in listdir(join(IMAGES_FOLDER, self.theme))
                    if file.endswith('.gif')]) - 2

    def load_cards(self) -> List[tk.PhotoImage]:

        total_nb = self.find_total_nb_cards_theme()

        ids_cards = list(range(1, total_nb + 1))
        chosen_cards = sample(ids_cards, k=self.cards_nb // 2)
        return [tk.PhotoImage(
            file=str(f'{IMAGES_FOLDER}/{self.theme}/carte-{str(card)}.gif'))
            for card in chosen_cards]

    def initiate_game(self) -> List[tk.PhotoImage]:

        memory_cards = self.load_cards() * 2
        return sample(memory_cards, k=len(memory_cards))


    # def set_up_theme_frame(self):
    #    self.cards_frame.destroy()
    #    self.main_frame.destroy()
    #    self.main_frame = tk.Frame(self.window, height=500, width=500)
    #    self.main_frame.grid(row=0, column=1)
    ##
    #    lab_message = tk.Label(
    #        master=self.main_frame,
    #        text="Choose the theme you want to play with "
    #    )
    ##
    #    lab_message.grid(row=0, column=2, columnspan=3)
    #    but_themes = [tk.Button(self.main_frame,
    #                            image=theme_card,
    #                            command=lambda x=count: self.start_theme(x)
    #                            )
    #                  for count, theme_card in enumerate(self.THEME_CARDS)]
    ##
    #    for count, but_theme in enumerate(but_themes):
    #        but_theme.grid(row=1, column=2 + count)

    def set_up_memory_frame(self):
        self.cards_frame.destroy()
        self.radio_buttons_frame.destroy()
        self.cards_frame = tk.Frame(self.window)
        self.cards_frame.grid(row=1, column=1)

        self.but_cards = [tk.Button(self.cards_frame,
                                    image=self.hidden_card,
                                    command=lambda x=i: self.show(x))
                          for i in range(self.cards_nb)]

        for count in range(self.cards_nb):
            self.but_cards[count].grid(row=count // self.game_dim[0],
                                       column=count % self.game_dim[0])

    def show_one_card(self, card_id):
        self.but_cards[card_id].configure(image=self.cards_ids[card_id])
        self.turned_cards_nb += 1
        self.turned_cards_ids.append(self.cards_ids[card_id])
        self.turned_card_played.append(card_id)


    def show(self, item):
        # if item not in self.found_cards and self.current_player.can_play:
        if item not in self.found_cards:
            if self.turned_cards_nb == 0:
                self.show_one_card(card_id=item)
            elif self.turned_cards_nb == 1:
                if item != self.turned_card_played[-1]:
                    self.show_one_card(card_id=item)
        if self.turned_cards_nb == 2:
            self.window.after(1000, self.check)

    def check(self):
        if self.turned_cards_nb != 2:
            return
        if self.turned_cards_ids[-1] == self.turned_cards_ids[-2]:
            self.found_cards.append(self.turned_card_played[-1])
            self.found_cards.append(self.turned_card_played[-2])
            self.but_cards[self.turned_card_played[-1]].configure(
                image=self.blank_card)
            self.but_cards[self.turned_card_played[-2]].configure(
                image=self.blank_card)
            self.increment_score_player()
            self.set_game_over()
        self.reinit()

    def reinit(self):
        for i in range(self.cards_nb):
            if i not in self.found_cards:
                self.but_cards[i].configure(image=self.hidden_card)
        self.turned_cards_nb = 0

    def start_new_game(self):
        self.display_stat_player()
        self.cards_ids = self.initiate_game()
        self.reset_game()
        self.set_up_memory_frame()
        if self.game_mode == 1:
            self.openbci.prepare_session()
            self.openbci.start_stream()

    #def start_theme(self):
    #    # self.theme = self.THEMES[x]
    #    self.hidden_card = tk.PhotoImage(
    #        file=f'{IMAGES_FOLDER}/{self.theme}/carte-0.gif')
    #    self.blank_card = tk.PhotoImage(
    #        file=f'{IMAGES_FOLDER}/{self.theme}/blankCard.gif'
    #    )
    #    self.start_new_game()

    # def display_players_score(self) -> None:
    #    """ Set up the frame with the names and scores of both players. """
    #    self.main_frame.destroy()
    #    self.main_frame = tk.Frame(self.window)
    #    self.main_frame.grid(row=0, column=1)
    #
    #    self.lab_player1 = tk.Label(
    #        master=self.main_frame,
    #        text=f' {self.player1.name.upper()} : ',
    #        font=("Helvetica", 20),
    #        fg='red'
    #    )
    #    self.lab_player1.grid(row=0, column=0)
    #
    #    self.lab_score_player1 = tk.Label(
    #        master=self.main_frame,
    #        text='0',
    #        font=("Helvetica", 20)
    #    )
    #    self.lab_score_player1.grid(row=0, column=1)
    #
    #    self.lab_player2 = tk.Label(
    #        master=self.main_frame,
    #        text=f' {self.player2.name.upper()} : ',
    #        font=("Helvetica", 20),
    #        fg='black'
    #    )
    #    self.lab_player2.grid(row=0, column=2)
    #
    #    self.lab_score_player2 = tk.Label(
    #        master=self.main_frame,
    #        text='0',
    #        font=("Helvetica", 20)
    #    )
    #    self.lab_score_player2.grid(row=0, column=3)

    def display_stat_player(self):
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self.window)
        self.main_frame.grid(row=0, column=1)

        self.lab_player = tk.Label(
            master=self.main_frame,
            text='Pairs of cards = ',
            font=("Helvetica", 20),
            fg='black'
        )
        self.lab_player.grid(row=0, column=0)

        self.lab_score_player = tk.Label(
            master=self.main_frame,
            text='0',
            font=("Helvetica", 20)
        )
        self.lab_score_player.grid(row=0, column=1)

    def increment_score_player(self) -> None:
        self.player.increment_score()
        self.lab_score_player.configure(text=str(self.player.score))

    #def set_dim_and_start(self, x):
    #    self.game_dim = self.DIMENSIONS[x]
    #    self.cards_nb = self.game_dim[0] * self.game_dim[1]
    #    self.start_new_game()
