import time
from turtle import Turtle, Screen
from paddle import Paddle
from ball import Ball
from scoreboard import Scoreboard
screen = Screen()
screen.listen()
scoreboard=Scoreboard()
screen.setup(width=800, height=600)
screen.title("Pong Game")
screen.bgcolor("black")
screen.tracer(0)
game_is_on = True
r_paddle = Paddle((370, 0))
l_paddle = Paddle((-370, 0))

ball = Ball()
screen.onkeypress(key="Down", fun=r_paddle.down)
screen.onkeypress(key="Up", fun=r_paddle.up)
screen.onkeypress(key="s", fun=l_paddle.down)
screen.onkeypress(key="w", fun=l_paddle.up)

while game_is_on:
    screen.update()
    time.sleep(ball.move_speed)
    ball.move()
    # Detect collision with wall
    if ball.ycor() > 280 or ball.ycor() < -275:
        ball.bounce_y()
    # Detect collision with paddle
    if ball.distance(r_paddle)<50 and ball.xcor()>345 or ball.distance(l_paddle)<50 and ball.xcor()<-345:
        ball.bounce_x()

    # Detect R paddle misses
    if ball.xcor()>383:
        ball.reset_position()
        scoreboard.r_point()

    # Detect L paddle misses
    if ball.xcor()<-384:
        ball.reset_position()
        scoreboard.l_point()









screen.exitonclick()
