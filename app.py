from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import *
from forms import *
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
db.create_all()
toolbar = DebugToolbarExtension(app)

@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = NewUserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username or email taken.  Please try agin')
            return render_template('register.html', form=form)
        session['user_id'] = new_user.id
        session['username']=new_user.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f'/users/{new_user.username}')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

app.route('/secret')
def show_secret():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    return render_template('secret.html')

@app.route('/users/<username>')
def show_secret(username):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    else:
        user = User.query.filter_by(username = username).first()
        return render_template('user.html', user=user)

@app.route('/logout')
def logout_user():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    session.pop('user_id')
    session.pop('username')
    flash("Goodbye!", "info")
    return redirect('/')

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    user = User.query.filter_by(username = username).first()
    if user.id == session['user_id']:
        db.session.delete(user)
        session.pop('user_id')
        session.pop('username')
        flash(f"{username} Deleted! We're sorry to see you go.", "danger")
        return redirect('/')
    else:
        flash("You're not allowed to do that.", 'danger')
        return redirect('/')

@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    user = User.query.filter_by(username = username).first()
    if user.id != session['user_id']:
        flash("You're not allowed to do that.", 'danger')
        return redirect('/')
    form = FeedbackForm()
    feedback = user.feedback
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=username)
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback Submitted!', 'success')
        return redirect(f'/users/{username}')
    return render_template('feedback-form.html', username=username, form=form)  

@app.route('/feedback/<int:fb_id>/update', methods=['GET', 'POST'])
def update_feedback(fb_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    fb = Feedback.query.get_or_404(fb_id)
    if fb.user.id != session['user_id']:
        flash("You're not allowed to do that.", 'danger')
        return redirect('/')
    
    form = FeedbackForm()
    if form.validate_on_submit():
        fb.title = form.title.data
        fb.content = form.content.data
        db.session.commit()
        flash('Feedback Updated!', 'info')
        return redirect(f'/users/{fb.user.username}')

    form.content.data = fb.content
    return render_template('edit-feedback.html', form=form, fb=fb)

@app.route('/feedback/<int:fb_id>/delete', methods=['POST'])
def delete_feedback(fb_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    fb = Feedback.query.get_or_404(fb_id)
    if fb.user.id == session['user_id']:
        db.session.delete(fb)
        db.session.commit()
        flash('Feedback Deleted!', 'info')
        return redirect(f'/users/{fb.user.username}')
    
    flash("You're not allowed to do that.", 'danger')
    return redirect('/')