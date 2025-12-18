from ensurepip import bootstrap

from flask import Flask, render_template,request
from form import ContactForm
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
app.secret_key="Hello YOU, This is my Secret Key"
bootstrap=Bootstrap5(app)

@app.route("/")
def home():
    return render_template('index.html')


@app.route("/login",methods=['POST','GET'])
def login():
    form = ContactForm()
    if form.validate_on_submit():
        if form.email.data=="admin@email.com" and form.password.data=="12345678":
            return render_template('success.html')
        else: return render_template('denied.html')
    return render_template('login.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
