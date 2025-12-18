from flask import Flask
import random
app=Flask("__name__")

random_number=0
@app.route('/')
def home():
    global random_number
    random_number=random.randint(0,9)
    print(random_number)
    return ("<h1>Guess a number between 0 and 9</h1>"
            "<img src='https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbm9oMWl4OW5xdmJxaWx6c2s3Mndhemg5N3RkanZ2MjhlM3h1dWc1MSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xUn3CftPBajoflzROU/giphy.gif'>")

@app.route('/<int:num>')
def guess_number(num):
    if num>random_number:
        return ("<h1 style='color: purple'>Too high, try again!</h1>" 
                "<img src='https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnJoaW10cTV4N3VpNnU1aHVvbjNmaDg0bXNkZGhiOHd3ZHFvMGFoZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KspzQl9Kx0pAJNCo8r/giphy.gif'>")

    if num<random_number:
        return ("<h1 style='color: red'>Too low, try again!</h1>"
                "<img src='https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXdzZ25tNDMwZjNuMjQxZGF5MW5jZnJvZ3UxbThrNXRqNnlpdnR3YSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/WfJyRpgey7o6HQi4Kk/giphy.gif'>")

    else:
        return "<h1 style='color: green'>You found me!</h1>" \
               "<img src='https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHhjcHFkcG8wczk4OGFtcXhjaTV2MjJzc214NzlkbzBpYnlhZ2pzayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oFzmkkwfOGlzZ0gxi/giphy.gif'>"



if __name__ == '__main__':
    app.run(debug=True)



