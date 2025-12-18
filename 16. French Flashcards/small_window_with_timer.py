from tkinter import *
import pandas
import random

BACKGROUND_COLOR = "#B1DDC6"
current_card = {}
to_learn = {}
timer_seconds = 3  # countdown seconds
countdown = timer_seconds
flip_timer = None

try:
    data = pandas.read_csv("data/words_to_learn.csv")
except FileNotFoundError:
    original_data = pandas.read_csv("data/french_words.csv")
    to_learn = original_data.to_dict(orient="records")
else:
    to_learn = data.to_dict(orient="records")


def update_timer():
    global countdown, flip_timer
    if countdown > 0:
        timer_label.config(text=f"Flip in: {countdown}s")
        countdown -= 1
        flip_timer = window.after(1000, update_timer)
    else:
        flip_card()
        timer_label.config(text="")  # Clear timer after flip


def next_card():
    global current_card, countdown, flip_timer
    if flip_timer:
        window.after_cancel(flip_timer)
    countdown = timer_seconds
    current_card = random.choice(to_learn)
    canvas.itemconfig(card_title, text="French", fill="black")
    canvas.itemconfig(card_word, text=current_card["French"], fill="black")
    canvas.itemconfig(card_background, image=card_front_img)
    update_timer()


def flip_card():
    canvas.itemconfig(card_title, text="English", fill="white")
    canvas.itemconfig(card_word, text=current_card["English"], fill="white")
    canvas.itemconfig(card_background, image=card_back_img)


def is_known():
    to_learn.remove(current_card)
    data = pandas.DataFrame(to_learn)
    data.to_csv("data/words_to_learn.csv", index=False)
    next_card()


window = Tk()
window.title("Flashy")
window.config(padx=20, pady=20, bg=BACKGROUND_COLOR)

card_front_img = PhotoImage(file="images/card_front_small.png")
card_back_img = PhotoImage(file="images/card_back_small.png")
cross_image = PhotoImage(file="images/wrong_small.png")
check_image = PhotoImage(file="images/right_small.png")

canvas = Canvas(width=400, height=263)
card_background = canvas.create_image(200, 131, image=card_front_img)
card_title = canvas.create_text(200, 75, text="", font=("Ariel", 20, "italic"))
card_word = canvas.create_text(200, 131, text="", font=("Ariel", 30, "bold"))
canvas.config(bg=BACKGROUND_COLOR, highlightthickness=0)
canvas.grid(row=0, column=0, columnspan=2)

timer_label = Label(text="", bg=BACKGROUND_COLOR, font=("Ariel", 15, "italic"))
timer_label.grid(row=1, column=0, columnspan=2, pady=(10,0))

unknown_button = Button(image=cross_image, highlightthickness=0, command=next_card)
unknown_button.grid(row=2, column=0)

known_button = Button(image=check_image, highlightthickness=0, command=is_known)
known_button.grid(row=2, column=1)

flip_timer = window.after(3000, func=flip_card)

next_card()

window.mainloop()
