import time
from turtle import Turtle


class Ball(Turtle):
    def __init__(self):
        super().__init__()
        self.shape("circle")
        self.penup()
        self.color("white")
        self.setheading(45)
        self.x_move = 3.8 * 3.2 * 0.7
        self.y_move = 2.8 * 3.2
        self.move_speed=0.1

        # self.shapesize(stretch_wid=1, stretch_len=5)
        # self.setheading(90)

    def move(self):
        # self.setx(self.xcor()+ self.x_move)
        # self.sety(self.ycor()+ self.y_move)
        new_x = self.xcor() + self.x_move
        new_y = self.ycor() + self.y_move
        self.goto(new_x, new_y)

    def bounce_y(self):
        self.y_move *= -1

    def bounce_x(self):
        self.x_move *= -1
        self.move_speed*=0.9

    def reset_position(self):
        self.move_speed=0.1
        self.goto(0,0)
        self.bounce_x()


