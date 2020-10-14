from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Email, Length, ValidationError
from flask_login import login_user, login_required, UserMixin, current_user, LoginManager, logout_user

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

db = SQLAlchemy(app)

# Inorder to use the login manager class
login_manager = LoginManager()

login_manager.init_app(app)

#It helps to redirect the user to login if not logged in
login_manager.login_view = 'login'

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=15, message='Must be more than 4 characters')])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80, message='Must me more than 7 characters')])

class SignupForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=5, max=15, message='Must be more than 4 characters')])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80, message='Must me more than 7 characters')])

class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    subtitle = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(20), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    content = db.Column(db.Text, nullable=False)

class Dogdata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    image_link = db.Column(db.Text, nullable=False)
    information = db.Column(db.Text, nullable=False)

# Usermixin is used to get access to the database to be used for login process
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    admin = db.Column(db.Boolean, default=False)

# it helps to reload user object from user_id
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Settin a default page for the index
@app.route('/', defaults={'page_num': 1})
@app.route('/<int:page_num>')
def index(page_num):
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).paginate(per_page=4, page=page_num, error_out=True)
    
    last_page = int(posts.pages)
    
    return render_template('index.html', posts=posts, last_page=last_page)


@app.route('/blogs/<int:post_id>')
def blogs(post_id):

    post = Blogpost.query.filter_by(id=post_id).one()

    date_posted = post.date_posted.strftime('%B %d, %Y')

    return render_template('blogs.html', post=post, date_posted=date_posted)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/addpost', methods=["POST", "GET"])
@login_required
def addpost():
    if request.method == "GET":
        return render_template('post.html')
    else:

        title = request.form['title']
        subtitle = request.form['subtitle']
        author = request.form['author']
        content = request.form['content']

        post = Blogpost(title=title, subtitle=subtitle, author=author, content=content, date_posted=datetime.now())
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('index'))

@app.route('/dogs', methods=["POST"])
def dogs():
    try:
        dog_name = request.form['dog-name']
        sentence = dog_name

        # converting the user input into lowercase with no spaces
        a = sentence.replace(" ", "").lower()

        result = Dogdata.query.filter_by(code=a).one()
    
        return render_template('dogs.html', result=result)
    except:
        return render_template('dogs.html', result=None)


@app.route('/adddog', methods=["POST", "GET"])
@login_required

def adddog():
    # allowing the access to only admin user
    if current_user.admin:
        if request.method == "POST":
            code = request.form['code']
            name = request.form['name']
            image_link = request.form['image_link']
            information = request.form['information']

            dog = Dogdata(code=code, name=name, image_link=image_link, information=information)
            db.session.add(dog)
            db.session.commit()

            return redirect(url_for('index'))
        else:
            return render_template('adddog.html')
    else:
        return "You do not have access"

@app.route('/signup', methods=["POST", "GET"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method="sha256")
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))
        
    return render_template('signup.html', form=form)

@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    message = "Username/Password is wrong"

    if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                if check_password_hash(user.password, form.password.data):
                    login_user(user)
                    return redirect(url_for('index'))
            
            return render_template('login.html', form=form, message=message)
    
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
