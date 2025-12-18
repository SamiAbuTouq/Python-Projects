from turtle import Turtle


class Paddle(Turtle):
    def __init__(self,pos):
        super().__init__()
        self.shape("square")
        self.penup()
        self.color("white")
        self.shapesize(stretch_wid=1, stretch_len=5)
        self.setheading(90)
        self.setpos(pos)
    def up(self):
        self.forward(25)

    def down(self):
        self.backward(25)
