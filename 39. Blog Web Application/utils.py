from flask import abort
from functools import wraps
from flask_login import current_user
import smtplib
import datetime
from models import Comment, db
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
EMAIL = os.getenv('MY_EMAIL')
PASSWORD = os.getenv('MY_EMAIL_PASSWORD')

# ---------------------------
# Helper Functions
# ---------------------------

def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(EMAIL, PASSWORD)
        connection.sendmail(to_addrs=EMAIL, from_addr=EMAIL, msg=email_message)


def calculate_time_difference(posted_time):
    current_time = datetime.datetime.now()
    diff = current_time - posted_time

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.email != 'admin@gmail.com':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def only_commenter(function):
    @wraps(function)
    def check(*args, **kwargs):
        user = db.session.execute(db.select(Comment).where(Comment.author_id == current_user.id)).scalar()
        if not current_user.is_authenticated or current_user.id != user.author_id:
            return abort(403)
        return function(*args, **kwargs)
    return check
