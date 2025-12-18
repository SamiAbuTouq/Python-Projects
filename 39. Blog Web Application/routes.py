from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from models import *
from forms import *
from utils import *

def init_routes(app):

    # ---------------------------
    # Home Page
    # ---------------------------
    @app.route('/')
    def get_all_posts():
        result = db.session.execute(db.select(BlogPost).order_by(BlogPost.title))
        posts = result.scalars().all()
        return render_template("index.html", all_posts=posts)

    # ---------------------------
    # Registration
    # ---------------------------
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
            if user:
                flash("You've already signed up with that email, log in instead!")
                return redirect(url_for('login'))

            hash_and_salted_password = generate_password_hash(
                password=form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                email=form.email.data,
                name=form.name.data,
                password=hash_and_salted_password
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(user=new_user)
            return redirect(url_for("get_all_posts"))
        return render_template("register.html", form=form)

    # ---------------------------
    # Login
    # ---------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
            if not user:
                flash("Email does not exist. Please try again.")
                return redirect(url_for('login'))
            if not check_password_hash(user.password, form.password.data):
                flash("Password incorrect. Please try again.")
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('get_all_posts'))
        return render_template("login.html", form=form)

    # ---------------------------
    # Logout
    # ---------------------------
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('get_all_posts'))

    # ---------------------------
    # Single Post & Comments
    # ---------------------------
    @app.route("/post/<int:post_id>", methods=["GET", "POST"])
    def show_post(post_id):
        post = db.get_or_404(BlogPost, post_id)
        form = CommentForm()
        if form.validate_on_submit():
            if not current_user.is_authenticated:
                flash("You need to login or register to comment.")
                return redirect(url_for("login"))
            new_comment = Comment(
                text=form.comment_text.data,
                comment_author=current_user,
                parent_post=post
            )
            db.session.add(new_comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=post_id))
        comments = Comment.query.filter_by(post_id=post_id).all()
        for c in comments:
            c.time_ago = calculate_time_difference(c.posted_time)
        return render_template("post.html", post=post, form=form, comments=comments)

    # ---------------------------
    # Create New Post (Admin Only)
    # ---------------------------
    @app.route("/new-post", methods=["GET", "POST"])
    @admin_only
    def add_new_post():
        form = CreatePostForm()
        if form.validate_on_submit():
            new_post = BlogPost(
                title=form.title.data,
                subtitle=form.subtitle.data,
                body=form.body.data,
                img_url=form.img_url.data,
                author=current_user,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for("get_all_posts"))
        return render_template("make-post.html", form=form)

    # ---------------------------
    # Edit Post (Admin Only)
    # ---------------------------
    @app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
    @admin_only
    def edit_post(post_id):
        post = db.get_or_404(BlogPost, post_id)
        form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            body=post.body
        )
        if form.validate_on_submit():
            post.title = form.title.data
            post.subtitle = form.subtitle.data
            post.img_url = form.img_url.data
            post.author = current_user
            post.body = form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
        return render_template("make-post.html", form=form, is_edit=True)

    # ---------------------------
    # Delete Post (Admin Only)
    # ---------------------------
    @app.route("/delete/<int:post_id>")
    @admin_only
    def delete_post(post_id):
        post = db.get_or_404(BlogPost, post_id)
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))

    # ---------------------------
    # About Page
    # ---------------------------
    @app.route("/about")
    def about():
        return render_template("about.html")

    # ---------------------------
    # Contact Page
    # ---------------------------
    @app.route('/contact', methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            data = request.form
            send_email(data["name"], data["email"], data["phone"], data["message"])
            return render_template("contact.html", msg_sent=True)
        return render_template("contact.html", msg_sent=False)

    # ---------------------------
    # Delete Comment (Only Commenter)
    # ---------------------------
    @app.route("/delete/comment/<int:comment_id>/<int:post_id>")
    @only_commenter
    def delete_comment(comment_id, post_id):
        comment = db.get_or_404(Comment, comment_id)
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
