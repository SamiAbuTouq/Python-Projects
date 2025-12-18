import random
from turtle import Turtle, Screen

is_race_one=False
screen = Screen()
screen.setup(width=500, height=400)
user_bet = screen.textinput(title="make your bet", prompt="Which turtle will win the race? Enter a color:")
colors = ["red", "blue", "green", "orange", "purple", "yellow"]
y_pos = [-100, -60, -20, 20, 60, 100]
all_turtle=[]
for i in range(0, 6):
    new_turtle = Turtle(shape="turtle")
    new_turtle.color(colors[i])
    new_turtle.penup()
    new_turtle.setpos(x=-230, y=y_pos[i])
    all_turtle.append(new_turtle)


if user_bet:
    is_race_one=True

while is_race_one:
    for turtle in all_turtle:
        if turtle.xcor()>210:
            is_race_one=False
            winning_color=turtle.pencolor()
            if user_bet==winning_color:
                print(f"you've won! The {winning_color} turtle is the winner!")
            else:
                print(f"you've lost! The {winning_color} turtle is the winner!")

        random_num=random.randint(0,10)
        turtle.forward(random_num)


screen.exitonclick()
