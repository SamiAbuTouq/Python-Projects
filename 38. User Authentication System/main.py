from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
# Database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
# Flask-Login
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# App Configuration
# ===============================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'


# Database Setup
# ===============================
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(1000))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))


with app.app_context():
    db.create_all()

# Flask-Login Setup
# ===============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects to /login if user tries to access a protected page (redirect unauthorized users)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Routes
# ===============================

# Home Page
@app.route('/')
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        result = db.session.execute(db.select(User).where(User.email == email))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        # Hash password
        hash_and_salted_password = generate_password_hash(
            password=request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )

        # Create new user
        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return render_template('secrets.html', name=new_user.name)
    return render_template("register.html", logged_in=current_user.is_authenticated)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user by email
        # user = User.query.filter_by(email=email).first() do the same as the following 2 lines
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()

        # Check if user exists
        if not user:
            flash("Email does not exist. Please try again.")
            return redirect(url_for('login'))

        # Check password
        if not check_password_hash(user.password, password):
            flash("Password incorrect. Please try again.")
            return redirect(url_for('login'))

        # Log the user in
        login_user(user)
        return redirect(url_for('secrets'))
    return render_template("login.html", logged_in=current_user.is_authenticated)


# Protected Secrets Page
@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html", name=current_user.name, logged_in=True)


# Protected Download Route
@app.route('/download')
@login_required
def download():
    return send_from_directory('static', path='files/cheat_sheet.pdf')


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Run App
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
