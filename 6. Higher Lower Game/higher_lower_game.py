from time import sleep
from art import logo, vs
from game_data import data
import random
import os


def profile():
    x = random.choice(data)
    name = x['name']
    follower_count = x['follower_count']
    description = x['description']
    country = x['country']
    compare = f"{name}, a {description}, from {country}."
    return compare, follower_count


def higher_lower():
    profile_a, followers_a = profile()
    profile_b, followers_b = profile()
    while followers_a == followers_b:
        profile_b, followers_b = profile()
    score = 0
    correct = True

    while correct:
        os.system('cls')
        print(logo)
        if score > 0:
            print(f"Correct! Your current score is: {score}.")

        print(f"Compare A: {profile_a}")
        print(vs)
        print(f"Compare B: {profile_b}")

        a_or_b = input("\nWho do you think has more followers? Type 'a', or 'b': ").lower()
        if a_or_b == 'a' and followers_a >= followers_b:
            score += 1
            profile_b, followers_b = profile()
        elif a_or_b == 'b' and followers_a <= followers_b:
            score += 1
            profile_a, followers_a = profile()
        else:
            print(f"\nIncorrect, your final score is {score}.")
            correct = False

    play_again = input("\nDo you want to play again? Type 'y' or 'n': ")
    if play_again == 'y':
        higher_lower()
    elif play_again == 'n':
        print("Thanks for playing!")


higher_lower()