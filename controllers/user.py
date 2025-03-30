from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from models.models import db, User, Subject, Chapter, Quiz, Score, Question
from sqlalchemy.orm import joinedload
import time
from datetime import datetime, timedelta
import logging

user_bp = Blueprint('user', __name__)

logging.basicConfig(level=logging.DEBUG)

@user_bp.route('/user_dashboard')
def user_dashboard():
    subjects = Subject.query.options(joinedload(Subject.chapters).joinedload(Chapter.quizzes)).all()
    current_time = datetime.now()
    available_quizzes = []
    upcoming_quizzes = []
    user_id = session.get('user_id')
    attempted_quiz_ids = []
    
    if user_id:
        attempted_quiz_ids = [score.quiz_id for score in Score.query.filter_by(user_id=user_id).all()]
    
    for subject in subjects:
        for chapter in subject.chapters:
            for quiz in chapter.quizzes:
                if quiz.id not in attempted_quiz_ids and quiz.posted:
                    if current_time >= quiz.date_of_quiz:
                        available_quizzes.append(quiz)
                    else:
                        upcoming_quizzes.append(quiz)

    return render_template('user_dashboard.html', 
                         available_quizzes=available_quizzes, 
                         upcoming_quizzes=upcoming_quizzes, 
                         Score=Score)

@user_bp.route('/subjects')
def list_subjects():
    subjects = Subject.query.all()
    return render_template('user_subjects.html', subjects=subjects)

@user_bp.route('/subject/<int:subject_id>/chapters')
def list_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('user_chapters.html', subject=subject, chapters=chapters)

@user_bp.route('/chapter/<int:chapter_id>/quizzes')
def list_quizzes(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template('user_quizzes.html', chapter=chapter, quizzes=quizzes, Score=Score)

@user_bp.route('/quiz/<int:quiz_id>')
def get_quiz_details(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)
    user_id = session.get('user_id')
    current_time = datetime.now()
    
    if user_id:
        existing_score = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).first()
        if existing_score:
            flash('You have already completed this quiz.', 'info')
            return redirect(url_for('user.user_dashboard'))
    
    if current_time < quiz.date_of_quiz:
        flash(f'This quiz will be available from {quiz.date_of_quiz.strftime("%Y-%m-%d %H:%M")}', 'info')
        return redirect(url_for('user.user_dashboard'))
    
    if session.get('quiz_id') and session.get('quiz_id') != quiz_id:
        flash('Please complete your current quiz first.', 'warning')
        return redirect(url_for('user.quiz_question', quiz_id=session['quiz_id']))
    
    return render_template('quiz_details.html', quiz=quiz)

@user_bp.route('/quiz/<int:quiz_id>/start')
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz_id'] = quiz_id
    session['start_time'] = time.time()
    session['end_time'] = time.time() + int(quiz.time_duration) * 60 
    session['questions'] = [q.id for q in quiz.questions]  
    session['score'] = 0
    return redirect(url_for('user.quiz_question', quiz_id=quiz_id))

@user_bp.route('/quiz/<int:quiz_id>/question')
def quiz_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    question_ids = session.get('questions')
    if not question_ids:
        return redirect(url_for('user.list_subjects'))

    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    time_left = session['end_time'] - time.time()
    if time_left <= 0:
        return redirect(url_for('user.submit_quiz', quiz_id=quiz_id))
    return render_template('quiz_question.html', quiz=quiz, questions=questions, time_left=int(time_left))

@user_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)
    questions = quiz.questions
    score = 0
    logging.debug(f"Quiz ID: {quiz_id}")

    for question in questions:
        selected_option = request.form.get(f'question_{question.id}')
        logging.debug(f"Question ID: {question.id}, Correct Option: {question.correct_option}, Selected Option: {selected_option}")
        if selected_option:
            if question.correct_option is not None:
                if str(selected_option) == str(question.correct_option):
                    score += 1
                    logging.debug("Correct answer selected!")
                else:
                    logging.debug("Incorrect answer selected.")
            else:
                logging.warning(f"Question ID: {question.id} has no correct option set.")
        else:
            logging.debug(f"No option selected for Question ID: {question.id}")

    total_score = score
    user_id = session.get('user_id')
    if user_id:
        new_score = Score(quiz_id=quiz_id, user_id=user_id, time_stamp_of_attempt=datetime.now(), total_scored=total_score)
        db.session.add(new_score)
        db.session.commit()

    session.pop('quiz_id', None)
    session.pop('start_time', None)
    session.pop('end_time', None)
    session.pop('questions', None)

    return render_template('quiz_result.html', total_score=total_score, quiz=quiz)

@user_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('user.user_dashboard'))

    now = datetime.now()
    user_id = session.get('user_id')

    quiz = Quiz.query.filter(Quiz.name.ilike(f'%{query}%'), Quiz.posted == True).first()
    if quiz:
        if user_id:
            existing_score = Score.query.filter_by(quiz_id=quiz.id, user_id=user_id).first()
            if not existing_score and now >= quiz.date_of_quiz:
                return redirect(url_for('user.get_quiz_details', quiz_id=quiz.id))

    subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
    quizzes = Quiz.query.filter(Quiz.name.ilike(f'%{query}%'), Quiz.posted == True).all()

    return render_template('search_results.html', 
                         query=query,
                         subjects=subjects, 
                         chapters=chapters, 
                         quizzes=quizzes,
                         Score=Score,
                         now=now)

@user_bp.route('/scores')
def scores():
    return render_template('user_scores.html', Score=Score)

@user_bp.route('/summary')
def summary():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    current_time = datetime.now()

    available_quizzes = Quiz.query.filter(
        Quiz.posted == True,
        Quiz.date_of_quiz <= current_time
    ).count()

    completed_count = Score.query.filter_by(user_id=user_id).count()

    completion_rate = round((completed_count / available_quizzes) * 100, 2) if available_quizzes > 0 else 0

    pending_count = available_quizzes - completed_count

    subjects = Subject.query.all()
    subject_names = []
    subject_scores = []
    all_scores = []
    highest_score = 0
    highest_quiz_name = ""
    lowest_score = 100
    lowest_quiz_name = ""
    total_score = 0
    score_count = 0

    for subject in subjects:
        total_subject_score = 0
        quiz_count = 0
        for chapter in subject.chapters:
            for quiz in chapter.quizzes:
                score = Score.query.filter_by(user_id=user_id, quiz_id=quiz.id).first()
                if score:
                    quiz_count += 1
                    score_percentage = (score.total_scored / len(quiz.questions)) * 100
                    total_subject_score += score_percentage
                    all_scores.append(score_percentage)
                    
                    # Update highest and lowest scores
                    if score_percentage > highest_score:
                        highest_score = score_percentage
                        highest_quiz_name = quiz.name
                    if score_percentage < lowest_score:
                        lowest_score = score_percentage
                        lowest_quiz_name = quiz.name
                    
                    total_score += score_percentage
                    score_count += 1

        subject_names.append(subject.name)
        if quiz_count > 0:
            subject_scores.append(round(total_subject_score / quiz_count, 2))
        else:
            subject_scores.append(0)

    average_score = round(total_score / score_count, 2) if score_count > 0 else 0

    if not all_scores:
        lowest_score = 0
        lowest_quiz_name = "No quizzes completed"
        highest_quiz_name = "No quizzes completed"

    return render_template('user_summary.html',
                         subject_names=subject_names,
                         subject_scores=subject_scores,
                         completed_count=completed_count,
                         pending_count=pending_count,
                         highest_score=round(highest_score, 2),
                         highest_quiz_name=highest_quiz_name,
                         lowest_score=round(lowest_score, 2),
                         lowest_quiz_name=lowest_quiz_name,
                         average_score=average_score,
                         completion_rate=completion_rate,
                         total_quizzes=available_quizzes)
