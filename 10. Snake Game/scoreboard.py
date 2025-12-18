from turtle import Turtle
ALIGNMENT="center"
FONT=('Courier', 19, 'normal')

class Scoreboard(Turtle):
    def __init__(self):
        self.score = 0
        super().__init__()
        self.color("white")
        self.penup()
        self.sety(260)
        self.update_scoreboard()
        self.hideturtle()

    def update_scoreboard(self):
        self.write(f"score = {self.score}", align=ALIGNMENT, font=FONT)

    def increase_score(self):
        self.clear()
        self.score += 1
        self.update_scoreboard()

    def game_over(self):
        self.goto(0,0)
        self.write("Game Over", align=ALIGNMENT, font=FONT)
