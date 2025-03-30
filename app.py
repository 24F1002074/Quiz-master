from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
from flask_sqlalchemy import SQLAlchemy
from models.models import db, User, Subject, Chapter, Quiz, Score  # Import db and User
from controllers.admin import admin
from controllers.user import user_bp 
from sqlalchemy.orm import joinedload
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_POOL_SIZE'] = 5

app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10

app.config['SQLALCHEMY_MAX_OVERFLOW'] = 10

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(admin, url_prefix='/admin')

app.register_blueprint(user_bp)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email.lower() == "admin@quizmaster.com" and password == "123":
            session['user_id'] = 0
            session['username'] = "Admin"
            session['just_logged_in'] = True
            session['subjects'] = [subject.id for subject in Subject.query.all()]
            session.modified = True
            return redirect(url_for('admin.admin_dashboard'))

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('user.user_dashboard'))
        else:
            flash("Invalid email or password", "error")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        dob = request.form['dob']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash("A user with this email already exists", "error")
            return render_template('register.html')

        if User.query.filter_by(phone=phone).first():
            flash("A user with this phone number already exists", "error")
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash("This username is already taken", "error")
            return render_template('register.html')

        new_user = User(username=username, email=email, phone=phone, dob=dob, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('quiz_id', None)
    session.pop('start_time', None)
    session.pop('end_time', None)
    session.pop('questions', None)
    session.pop('score', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
