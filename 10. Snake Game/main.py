import time
from turtle import Screen

from scoreboard import Scoreboard
from snake import Snake
from food import Food

screen = Screen()
screen.listen()
screen.setup(width=600, height=600)
screen.bgcolor("black")
screen.tracer(0)
segments = []

snake = Snake()
food = Food()
scoreboard = Scoreboard()
screen.listen()
screen.onkey(snake.right, "Right")
screen.onkey(snake.up, "Up")
screen.onkey(snake.left, "Left")
screen.onkey(snake.down, "Down")

# Parameter Info: When inside a function call like range( → press Ctrl + P to see the expected parameters.
# Structure Tool Window Alt + 7.
game_is_on = True
while game_is_on:
    screen.update()
    time.sleep(0.08)
    snake.move()

    # Detect collision with food
    if snake.head.distance(food) < 12:
        food.refresh()
        snake.extend()
        scoreboard.increase_score()

    # Detect collision with wall
    if snake.head.xcor()>290 or snake.head.xcor()<-295 or snake.head.ycor()>295 or snake.head.ycor()<-295:
        game_is_on=False
        scoreboard.game_over()

    # Detect collision with tail
    # if head collides with any segment of the tail
    for segment in snake.segments[1:]:
        if snake.head.distance(segment)<10:
            game_is_on=False
            scoreboard.game_over()


screen.title("My Snake Game")

screen.exitonclick()
