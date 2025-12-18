from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_gravatar import Gravatar
from models import db
from routes import init_routes
from dotenv import load_dotenv
import os

# ---------------------------
# Flask App Initialization
# ---------------------------
app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI','sqlite:///posts.db')
app.config['CKEDITOR_SERVE_LOCAL'] = True

# ---------------------------
# Extensions
# ---------------------------
Bootstrap5(app)
CKEditor(app)
db.init_app(app)

gravatar = Gravatar(
    app,
    size=150,
    rating='pg',
    default='robohash',
    force_default=False,
    use_ssl=True
)

# ---------------------------
# Flask-Login Configuration
# ---------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User  # Import User here for loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Initialize Routes
# ---------------------------
init_routes(app)

# ---------------------------
# Create Database Tables
# ---------------------------
with app.app_context():
    db.create_all()

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
