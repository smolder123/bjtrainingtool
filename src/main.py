from random import choice
from PIL import Image, ImageTk
from time import time
from tkinter import ttk
import tkinter as tk
import os
import sys


def blackjack_total(hand, card_values):
    values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "1": 10, "a": 11}

    total = 0
    aces = 0

    for card in hand:
        card_value = values[card_values[card['image']]]
        total += card_value
        if card_value == 11:
            aces += 1

    original_aces = aces  # Track original number of aces
    while total > 21 and aces:
        total -= 10
        aces -= 1

    is_hard = original_aces == 0 or aces == 0

    return total, "hard" if is_hard else "soft"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_images():
    identify_image = {}
    images = []
    images_no_10s = []
    asset_folder = resource_path("assets")
    for filename in os.listdir(asset_folder):
        first_char = filename[0]
        img = Image.open(resource_path(f"assets/{filename}"))
        img_tk = ImageTk.PhotoImage(img)
        identify_image[str(img_tk)] = first_char

        images.append(img_tk)
        if first_char != '1':
            images_no_10s.append(img_tk)

    return images, images_no_10s, identify_image

def add_card_to_hand(root, coords, cards, faceup=True):
    if faceup:
        new_card = choice(cards[:-1])
        new_label = tk.Label(root, image=new_card, background='light gray')
    else:
        new_label = tk.Label(root, image=cards[-1], background='light gray')

    new_label.place(x=coords[0], y=coords[1])
    return new_label

def play_hand(root, card_info, le_slider, hl, tens_var):
    start_time = time()
    cards_with_10s, cards_no_10s, identify_hand = card_info

    tens = tens_var.get()
    if tens:
        cards = cards_with_10s
    else:
        cards = cards_no_10s

    dealer_hand = [add_card_to_hand(root, [510, 52], cards, False), add_card_to_hand(root, [340, 52], cards)]
    player_hand = [[add_card_to_hand(root, [395, 530], cards), add_card_to_hand(root, [425, 500], cards)]]

    dealer_up_card_value = identify_hand[dealer_hand[1]['image']]
    dealer_bj_total = 0

    down_arrow = tk.Label(root, text='↓', font=("Arial", 24), bg='light gray')

    hand_coords = {1: [[395, 530]], 2: [[195, 530], [595, 530]], 3: [[115, 530], [395, 530], [715, 530]], 4: [[95, 530], [308, 530], [523, 530], [735, 530]]}

    hand_index = -1
    win_lose_index = -1

    def win_or_lose(event, dealer_total):
        nonlocal win_lose_index

        player_hand_total, _ = blackjack_total(player_hand[win_lose_index], identify_hand)
        if player_hand_total > 21:
            player_hand_total = -2

        key_pressed = event.keysym
        if key_pressed == 'Down':
            if player_hand_total > dealer_total:
                flash_arrow(root, down_arrow, 'green')
            else:
                flash_arrow(root, down_arrow, 'red')
        elif key_pressed == 'Up':
            if dealer_total > player_hand_total:
                flash_arrow(root, down_arrow, 'green')
            else:
                flash_arrow(root, down_arrow, 'red')
        elif key_pressed == 'Right' or key_pressed == 'Left':
            if dealer_total == player_hand_total:
                flash_arrow(root, down_arrow, 'green')
            else:
                flash_arrow(root, down_arrow, 'red')
        else:
            return 1

        win_lose_index -= 1

        if abs(win_lose_index) > len(player_hand):
            root.unbind("<Key>")
            root.after(get_dealing_speed(le_slider), lambda: reset_hand(root, card_info, le_slider, dealer_hand, player_hand, down_arrow, start_time, hl, tens_var))
        else:
            down_arrow_coords = hand_coords[len(player_hand)][win_lose_index].copy()
            down_arrow.place(x=down_arrow_coords[0] + 65, y=350)

    def dealer_turn():
        nonlocal dealer_hand
        start_coords = [340, 52]
        dealer_hand[0].destroy()
        dealer_hand[0] = add_card_to_hand(root, [510, 52], cards)
        dealer_hand[0].lower()
        down_arrow.place_forget()

        def nested_dealer():
            nonlocal dealer_bj_total
            bj_total, soft_hard = blackjack_total(dealer_hand, identify_hand)
            if (bj_total >= 17 and soft_hard == 'hard') or (bj_total >= 18 and soft_hard == 'soft'):
                down_arrow_coords = hand_coords[len(player_hand)][win_lose_index].copy()
                down_arrow.place(x=down_arrow_coords[0] + 65, y=350)
                if bj_total > 21:
                    dealer_bj_total = -1
                else:
                    dealer_bj_total = bj_total
                root.bind("<Key>", lambda event: win_or_lose(event, dealer_bj_total))
                return 1

            if len(dealer_hand) <= 3:
                start_coords[0] -= 160
                dealer_hand.append(add_card_to_hand(root, start_coords, cards))
            else:
                dealer_hand.append(add_card_to_hand(root, start_coords, cards))
                move_dealer_cards(dealer_hand)

            root.after(get_dealing_speed(le_slider), nested_dealer)
        root.after(get_dealing_speed(le_slider), nested_dealer)


    def playing_decision(event):
        nonlocal hand_index
        nonlocal player_hand

        base_card_coords = hand_coords[len(player_hand)][hand_index].copy()

        for i in range(len(player_hand[hand_index])):
            base_card_coords[0] += 30
            base_card_coords[1] -= 30

        player_hand, decrement = handle_playing_decision(event, root, cards, player_hand, dealer_up_card_value, hand_index, base_card_coords, hand_coords, identify_hand, down_arrow)

        hand_index -= decrement

        if abs(hand_index) > len(player_hand):
            root.unbind("<Key>")
            root.after(get_dealing_speed(le_slider), dealer_turn)
        else:
            down_arrow_coords = hand_coords[len(player_hand)][hand_index].copy()
            down_arrow.place(x=down_arrow_coords[0] + 65, y=350)

    down_arrow.place(x=460, y=350)
    root.bind("<Key>", playing_decision)

def flash_arrow(root, arrow, color):
    arrow.config(fg=color)
    root.after(200, lambda: arrow.config(fg="black"))

def handle_playing_decision(event, root, cards, player_hand, dealer_up_card, index, place_card_at_coords, hand_coords, card_values, down_arrow):
    current_hand = player_hand[index]
    key_pressed = event.keysym
    bj_total = blackjack_total(current_hand, card_values)
    current_hand_len = len(current_hand)
    if key_pressed == 'q':  # hit
        check_basic_strategy(root, bj_total, dealer_up_card, 'H', current_hand_len, down_arrow)
        current_hand += [add_card_to_hand(root, place_card_at_coords, cards)]
        new_total, _ = blackjack_total(current_hand, card_values)
        if new_total > 21:
            return player_hand, 1
        return player_hand, 0
    elif key_pressed == 'w':  # stand
        check_basic_strategy(root, bj_total, dealer_up_card, 'S', current_hand_len, down_arrow)
        return player_hand, 1
    elif key_pressed == 'e':  # double
        if current_hand_len == 2:
            check_basic_strategy(root, bj_total, dealer_up_card, 'D', current_hand_len, down_arrow)
            current_hand += [add_card_to_hand(root, place_card_at_coords, cards)]
            return player_hand, 1
        return player_hand, 0
    elif key_pressed == 'r':  # split
        num_splits = len(player_hand) - 1
        first_card_image = card_values[current_hand[0]['image']]
        if num_splits == 3 and current_hand_len == 2 or first_card_image != card_values[current_hand[1]['image']]:
            return player_hand, 0
        elif num_splits < 3:
            check_basic_strategy(root, first_card_image, dealer_up_card, 'P', current_hand_len, down_arrow)
            current_hand = [[current_hand[0], add_card_to_hand(root, [1, 1], cards)],
                            [current_hand[1], add_card_to_hand(root, [1, 1], cards)]]
            player_hand[index:index] = current_hand
            player_hand.pop(index)
            move_cards(hand_coords, player_hand)
            return player_hand, 0
    else:
        return player_hand, 0

def move_cards(base_coords, cards):
    hand_coords = base_coords[len(cards)]
    for index, coord in enumerate(hand_coords):
        copied_coord = coord.copy()
        cards[index][0].place(x=copied_coord[0], y=copied_coord[1])
        for card in cards[index][1:]:
            copied_coord[0] += 30
            copied_coord[1] -= 30
            card.place(x=copied_coord[0], y=copied_coord[1])

def move_dealer_cards(dealer_hand):
    len_dealer_hand = len(dealer_hand)
    space_between_cards = round((510-20)/(len_dealer_hand-1))
    starting_coord = 510
    for card in dealer_hand:
        card.place(x=starting_coord, y=52)
        starting_coord -= space_between_cards

def get_dealing_speed(tk_slider):
    deal_speed = lambda x: -167 * (x-1) + 2000
    return round(deal_speed(tk_slider.get()))

def reset_hand(root, card_images, slider_value, dealer_hand, player_hand, down_arrow, start_time, h_label, tens_var):
    for card in dealer_hand:
        card.place_forget()
        card.destroy()
    dealer_hand.clear()

    num_player_hands = len(player_hand)
    for hands in player_hand:
        for card in hands:
            card.place_forget()
            card.destroy()
    player_hand.clear()

    down_arrow.place_forget()
    down_arrow.destroy()
    root.update_idletasks()

    h_label['text'] = f'{round((time()-start_time)/num_player_hands, 1)} s/hand'

    root.after(500, lambda: play_hand(root, card_images, slider_value, h_label, tens_var))

def check_basic_strategy(root, player_hand, dealer_up_card, player_decision, player_hand_length, down_arrow):
    basic_strategy = {
        'pair': {
            'a': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'P', '9': 'P', '1': 'P', 'a': 'P'},
            '1': {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            '9': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'S', '8': 'P', '9': 'P', '1': 'S', 'a': 'S'},
            '8': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'P', '9': 'P', '1': 'P', 'a': 'P'},
            '7': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            '6': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            '5': {'2': 'D', '3': 'D', '4': 'D', '5': 'D', '6': 'D', '7': 'D', '8': 'D', '9': 'D', '1': 'H', 'a': 'H'},
            '4': {'2': 'H', '3': 'H', '4': 'H', '5': 'P', '6': 'P', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            '3': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            '2': {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'}
        },
        'soft': {
            21: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            20: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            19: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': ['D', 'S'], '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            18: {'2': ['D', 'S'], '3': ['D', 'S'], '4': ['D', 'S'], '5': ['D', 'S'], '6': ['D', 'S'], '7': 'S', '8': 'S', '9': 'H', '1': 'H', 'a': 'H'},
            17: {'2': 'H', '3': 'D', '4': 'D', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            16: {'2': 'H', '3': 'H', '4': 'D', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            15: {'2': 'H', '3': 'H', '4': 'D', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            14: {'2': 'H', '3': 'H', '4': 'H', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            13: {'2': 'H', '3': 'H', '4': 'H', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            12: {'2': 'P', '3': 'P', '4': 'P', '5': 'P', '6': 'P', '7': 'P', '8': 'P', '9': 'P', '1': 'P', 'a': 'P'}
        },
        'hard': {
            21: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            20: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            19: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            18: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            17: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'S', '8': 'S', '9': 'S', '1': 'S', 'a': 'S'},
            16: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            15: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            14: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            13: {'2': 'S', '3': 'S', '4': 'S', '5': 'S', '6': 'S', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            12: {'2': 'H', '3': 'H', '4': 'S', '5': 'S', '6': 'S', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            11: {'2': 'D', '3': 'D', '4': 'D', '5': 'D', '6': 'D', '7': 'D', '8': 'D', '9': 'D', '1': 'D', 'a': 'D'},
            10: {'2': 'D', '3': 'D', '4': 'D', '5': 'D', '6': 'D', '7': 'D', '8': 'D', '9': 'D', '1': 'H', 'a': 'H'},
            9: {'2': 'H', '3': 'D', '4': 'D', '5': 'D', '6': 'D', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            8: {'2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            7: {'2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            6: {'2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            5: {'2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'},
            4: {'2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H', '7': 'H', '8': 'H', '9': 'H', '1': 'H', 'a': 'H'}
        }
    }

    # doesnt check split table if hitting or standing two of the same cards (bug)
    if player_decision == 'P':
        correct_decision = basic_strategy['pair'][player_hand][dealer_up_card]
    elif player_decision == 'H':
        correct_decision = basic_strategy[player_hand[1]][player_hand[0]][dealer_up_card]
        if type(correct_decision) is not list and player_hand_length > 2:
            if correct_decision == 'D':
                correct_decision = 'H'
        elif type(correct_decision) is list and player_hand_length > 2:
            correct_decision = 'S'
        elif type(correct_decision) is list and player_hand_length == 2:
            correct_decision = 'H'
    elif player_decision == 'S':
        correct_decision = basic_strategy[player_hand[1]][player_hand[0]][dealer_up_card]
        if type(correct_decision) is list and player_hand_length > 2:
            correct_decision = 'S'
        elif type(correct_decision) is list and player_hand_length == 2:
            correct_decision = 'D'
    elif player_decision == 'D':
        correct_decision = basic_strategy[player_hand[1]][player_hand[0]][dealer_up_card]
        if type(correct_decision) is list:
            correct_decision = 'D'
    else:
        return 1

    if player_decision != correct_decision:
        flash_arrow(root, down_arrow, 'red')
    else:
        flash_arrow(root, down_arrow, 'green')

def le_help():
    new_window = tk.Toplevel()
    new_window.title('Help')
    le_message = """q = hit\nw = stand\ne = double\nr = split\n\nThe arrow shows which hand you are currrently making a decision on. The on/off is for enabling/disabling tens in the deck; it's good for practicing those 5+ card hands. After making a decision on all hands, the arrow will go back through each hand. Press either 'up' (dealer wins), 'down' (player wins), or 'left' or 'right' (dealer and player push). The arrow will flash red or green depending on if you either make a basic strategy error, or you determine who wins/loses incorrectly.\n\nDifferences between normal bj: dealer will not check for 10/ace if ace/10 is showing. Dealer will still draw to hard 17/soft 18 even if player busts. You can make playing decisions on split aces."""
    message = tk.Message(new_window, text=le_message, width=600, font=("Arial", 15), justify="center")
    message.pack(padx=100, pady=10)

def main():
    root = tk.Tk()
    root.geometry("1000x800")
    root.title('Bj training tool')
    card_images = load_images()
    root.configure(background='light gray')

    game_rules = tk.Label(root, text="H17 DaS RSA No Surrender No Insurance", bg="light gray")
    game_rules.place(relx=1.0, y=2, anchor='ne')

    close_button = ttk.Button(root, text="Give up.", command=root.destroy)
    close_button.place(relx=1.0, x=-10, y=25, anchor="ne")

    help_button = ttk.Button(root, text="?", width=3, command=le_help)
    help_button.place(relx=1.0, x=-90, y=25, anchor="ne")

    slider_value = tk.IntVar(value=5)

    slider = tk.Scale(root, from_=1, to=10, orient='horizontal', variable=slider_value, length=210)
    slider.place(relx=1.0, y=55, anchor='ne')

    hand_time_label = tk.Label(root, text="", bg="light gray", font=("Arial", 12))
    hand_time_label.place(x=835, y=200)

    tens_var = tk.BooleanVar(value=True)
    toggle_btn = ttk.Checkbutton(root, text="ON", variable=tens_var, command=lambda: toggle_btn.config(text="ON" if tens_var.get() else "OFF"), style="Toggle.TButton", width=7)
    toggle_btn.place(relx=1.0, x=-122, y=25, anchor="ne")

    play_hand(root, card_images, slider_value, hand_time_label, tens_var)

    root.mainloop()

if __name__ == '__main__':
    main()
