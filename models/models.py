from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    # Add cascade='all, delete-orphan' to automatically delete related chapters
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade='all, delete-orphan')

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Chapter {self.name}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Add name field
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable=False)  # Changed from Date to DateTime
    time_duration = db.Column(db.String(10))  # Store as HH:MM
    remarks = db.Column(db.Text)
    posted = db.Column(db.Boolean, default=False)  # Add posted field

    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Quiz {self.id} - {self.chapter_id}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))
    correct_option = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Question {self.id}>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, nullable=False)
    total_scored = db.Column(db.Integer, nullable=False)

    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f'<Score {self.total_scored}>'
