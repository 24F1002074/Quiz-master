from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify, session, flash
from models.models import db, Subject, Chapter, Quiz, Question, User, Score
from sqlalchemy.orm import joinedload
from datetime import datetime
import logging

admin = Blueprint('admin', __name__)

logging.basicConfig(level=logging.DEBUG)

@admin.route('/admin/dashboard')
def admin_dashboard():
    subjects = Subject.query.options(joinedload(Subject.chapters).joinedload(Chapter.quizzes)).all()
    
    total_chapters = sum(len(subject.chapters) for subject in subjects)
    total_quizzes = sum(len([quiz for chapter in subject.chapters for quiz in chapter.quizzes]) for subject in subjects)
    total_users = User.query.count()
    
    if 'just_logged_in' in session:
        session.pop('just_logged_in')
        
    return render_template('admin_dashboard.html', subjects=subjects, total_chapters=total_chapters, total_quizzes=total_quizzes, total_users=total_users)

@admin.route('/admin/manage_subjects')
def manage_subjects():
    subjects = Subject.query.options(joinedload(Subject.chapters)).all()
    return render_template('manage_subjects.html', subjects=subjects)

@admin.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name and description:
            new_subject = Subject(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            db.session.flush()
        else:
            pass

    return redirect(url_for('admin.manage_subjects'))

@admin.route('/admin/update_subject', methods=['GET', 'POST'])
def update_subject():
    if request.method == 'POST':
        subject_id = request.form.get('id')
        name = request.form.get('name')
        description = request.form.get('description')

        subject = Subject.query.get(subject_id)
        if subject and name and description:
            subject.name = name
            subject.description = description
            db.session.commit()
        else:
            pass

    return redirect(url_for('admin.manage_subjects'))

@admin.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if subject:
        try:
            chapters = Chapter.query.filter_by(subject_id=subject_id).all()
            for chapter in chapters:
                quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
                for quiz in quizzes:
                    db.session.delete(quiz)
                db.session.delete(chapter)

            db.session.delete(subject)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            pass

    return redirect(url_for('admin.manage_subjects'))

@admin.route('/admin/add_chapter/<int:subject_id>', methods=['POST'])
def add_chapter(subject_id):
    try:
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name or not description:
            pass
            return redirect(url_for('admin.manage_chapters', subject_id=subject_id))

        new_chapter = Chapter(
            name=name,
            description=description,
            subject_id=subject_id
        )
        
        db.session.add(new_chapter)
        db.session.commit()
        return redirect(url_for('admin.manage_chapters', subject_id=subject_id))
        
    except Exception as e:
        db.session.rollback()
        pass
        
    return redirect(url_for('admin.manage_chapters', subject_id=subject_id))

@admin.route('/admin/update_chapter/<int:chapter_id>', methods=['POST'])
def update_chapter(chapter_id):
    try:
        chapter = Chapter.query.get_or_404(chapter_id)
        name = request.form.get('name')
        description = request.form.get('description')
        
        if name and description:
            chapter.name = name
            chapter.description = description
            db.session.commit()
            
        return redirect(url_for('admin.manage_chapters', subject_id=chapter.subject_id))
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating chapter: {str(e)}")
        
    return redirect(url_for('admin.manage_chapters', subject_id=chapter.subject_id))

@admin.route('/admin/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    try:
        chapter = Chapter.query.get_or_404(chapter_id)
        subject_id = chapter.subject_id
        db.session.delete(chapter)
        db.session.commit()
        return redirect(url_for('admin.manage_chapters', subject_id=subject_id))
    except Exception as e:
        db.session.rollback()
        pass
    
    return redirect(url_for('admin.manage_subjects'))

@admin.route('/admin/create_quiz/<int:chapter_id>', methods=['GET', 'POST'])
def create_quiz(chapter_id):
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            duration = request.form.get('duration')
            date_of_quiz = datetime.strptime(request.form.get('date_of_quiz'), '%Y-%m-%dT%H:%M')
            remarks = request.form.get('remarks')
            
            quiz = Quiz(
                name=name,
                chapter_id=chapter_id,
                time_duration=duration,
                date_of_quiz=date_of_quiz,
                remarks=remarks
            )
            db.session.add(quiz)
            db.session.commit()
            
            questions = request.form.getlist('questions[]')
            options1 = request.form.getlist('options1[]')
            options2 = request.form.getlist('options2[]')
            options3 = request.form.getlist('options3[]')
            options4 = request.form.getlist('options4[]')
            correct_options = request.form.getlist('correct_options[]')
            
            for i in range(len(questions)):
                question = Question(
                    quiz_id=quiz.id,
                    question_statement=questions[i],
                    option1=options1[i],
                    option2=options2[i],
                    option3=options3[i] if i < len(options3) else None,
                    option4=options4[i] if i < len(options4) else None,
                    correct_option=correct_options[i]
                )
                db.session.add(question)
            
            db.session.commit()
            return redirect(url_for('admin.manage_quizzes', chapter_id=chapter_id))
        except Exception as e:
            db.session.rollback()
            pass
    
    chapter = Chapter.query.get_or_404(chapter_id)
    return render_template('create_quiz.html', chapter=chapter)

@admin.route('/admin/edit_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    if request.method == 'POST':
        try:
            quiz.name = request.form.get('name')
            quiz.time_duration = request.form.get('duration')
            date_of_quiz_str = request.form.get('date_of_quiz')
            if date_of_quiz_str:
                quiz.date_of_quiz = datetime.strptime(date_of_quiz_str, '%Y-%m-%dT%H:%M')
            else:
                flash("Date and Time cannot be empty.", "error")
                return render_template('edit_quiz.html', chapter=quiz.chapter, quiz=quiz)
            quiz.remarks = request.form.get('remarks')
            
            question_ids = request.form.getlist('question_ids[]')
            questions = request.form.getlist('questions[]')
            options1 = request.form.getlist('options1[]')
            options2 = request.form.getlist('options2[]')
            options3 = request.form.getlist('options3[]')
            options4 = request.form.getlist('options4[]')
            correct_options = request.form.getlist('correct_options[]')
            
            for i in range(len(questions)):
                if question_ids and i < len(question_ids) and question_ids[i]:
                    question = Question.query.get(question_ids[i])
                    if question:
                        question.question_statement = questions[i]
                        question.option1 = options1[i]
                        question.option2 = options2[i]
                        question.option3 = options3[i] if i < len(options3) else None
                        question.option4 = options4[i] if i < len(options4) else None
                        question.correct_option = correct_options[i]

            new_questions = request.form.getlist('new_questions[]')
            new_options1 = request.form.getlist('new_options1[]')
            new_options2 = request.form.getlist('new_options2[]')
            new_options3 = request.form.getlist('new_options3[]')
            new_options4 = request.form.getlist('new_options4[]')
            new_correct_options = request.form.getlist('new_correct_options[]')

            for i in range(len(new_questions)):
                question = Question(
                    quiz_id=quiz_id,
                    question_statement=new_questions[i],
                    option1=new_options1[i],
                    option2=new_options2[i],
                    option3=new_options3[i] if i < len(new_options3) else None,
                    option4=new_options4[i] if i < len(new_options4) else None,
                    correct_option=new_correct_options[i]
                )
                db.session.add(question)

            deleted_question_ids = request.form.getlist('deleted_question_ids[]')
            for question_id in deleted_question_ids:
                question_to_delete = Question.query.get(question_id)
                if question_to_delete:
                    db.session.delete(question_to_delete)
            
            db.session.commit()
            return redirect(url_for('admin.manage_quizzes', chapter_id=chapter_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating quiz: {e}", 'error')
            return render_template('edit_quiz.html', chapter=quiz.chapter, quiz=quiz)
    
    return render_template('edit_quiz.html', chapter=quiz.chapter, quiz=quiz)

@admin.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        chapter_id = quiz.chapter_id 
        db.session.delete(quiz)
        db.session.commit()
        return redirect(url_for('admin.manage_quizzes', chapter_id=chapter_id))
    except Exception as e:
        db.session.rollback()
        pass
    
    return redirect(url_for('admin.manage_quizzes', chapter_id=chapter_id))

@admin.route('/admin/post_quiz/<int:quiz_id>', methods=['POST'])
def post_quiz(quiz_id):
    try:
        quiz = Quiz.query.get_or_404(quiz_id)
        quiz.posted = True
        db.session.commit()
        referrer = request.referrer
        if 'manage_all_quizzes' in referrer:
            return redirect(url_for('admin.manage_all_quizzes'))
        return redirect(url_for('admin.manage_quizzes', chapter_id=quiz.chapter_id))
    except Exception as e:
        db.session.rollback()
        pass
    
    # Default fallback
    return redirect(url_for('admin.manage_quizzes', chapter_id=quiz.chapter_id))

@admin.route('/admin/manage_chapters/<int:subject_id>')
def manage_chapters(subject_id):
    subject = Subject.query.options(
        joinedload(Subject.chapters).joinedload(Chapter.quizzes)
    ).get_or_404(subject_id)
    return render_template('manage_chapters.html', subject=subject, chapters=subject.chapters)

@admin.route('/admin/manage_users')
def manage_users():
    users = User.query.all()
    subjects = Subject.query.all()
    user_scores = {}
    
    for user in users:
        user_scores[user.id] = {}
        for subject in subjects:
            total_score = 0
            quiz_count = 0
            for chapter in subject.chapters:
                for quiz in chapter.quizzes:
                    score = Score.query.filter_by(user_id=user.id, quiz_id=quiz.id).first()
                    if score:
                        total_score += score.total_scored
                        quiz_count += 1
            if quiz_count > 0:
                user_scores[user.id][subject.id] = total_score / quiz_count
            else:
                user_scores[user.id][subject.id] = 0
    
    return render_template('manage_users.html', users=users, subjects=subjects, user_scores=user_scores)

@admin.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        try:
            Score.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            pass
    
    return redirect(url_for('admin.manage_users'))

@admin.route('/admin/manage_quizzes/<int:chapter_id>')
def manage_quizzes(chapter_id):
    chapter = Chapter.query.options(joinedload(Chapter.quizzes)).get_or_404(chapter_id)
    return render_template('manage_quizzes.html', chapter=chapter)

@admin.route('/admin/manage_all_quizzes')
def manage_all_quizzes():
    subjects = Subject.query.options(
        joinedload(Subject.chapters).joinedload(Chapter.quizzes)
    ).all()
    return render_template('all_quizzes.html', subjects=subjects)

@admin.route('/admin/show_quiz/<int:quiz_id>')
def show_quiz(quiz_id):
    quiz = Quiz.query.options(joinedload(Quiz.questions)).get_or_404(quiz_id)
    chapter = quiz.chapter
    return render_template('show_quiz.html', quiz=quiz, chapter=chapter)

@admin.route('/admin/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('admin.admin_dashboard'))
    
    subject = Subject.query.filter(Subject.name.ilike(f'%{query}%')).first()
    if subject:
        return redirect(url_for('admin.manage_chapters', subject_id=subject.id))

    chapter = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).first()
    if chapter:
        return redirect(url_for('admin.manage_quizzes', chapter_id=chapter.id))

    quiz = Quiz.query.filter(Quiz.name.ilike(f'%{query}%')).first()
    if quiz:
        return redirect(url_for('admin.show_quiz', quiz_id=quiz.id))

    flash(f'No results found for "{query}"', 'error')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/admin/summary')
def summary():
    subjects = Subject.query.all()
    subject_names = [subject.name for subject in subjects]
    
    quiz_counts = []
    subject_averages = []
    attempt_counts = []
    success_rates = [] 
    
    for subject in subjects:
        quiz_count = 0
        total_percentage = 0
        total_attempts = 0
        successful_attempts = 0
        
        for chapter in subject.chapters:
            chapter_quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
            quiz_count += len(chapter_quizzes)
            
            for quiz in chapter_quizzes:
                scores = Score.query.filter_by(quiz_id=quiz.id).all()
                attempt_count = len(scores)
                total_attempts += attempt_count
                
                for score in scores:
                    if quiz.questions: 
                        score_percentage = (score.total_scored / len(quiz.questions)) * 100
                        total_percentage += score_percentage
                        if score_percentage > 75:
                            successful_attempts += 1

        quiz_counts.append(quiz_count)
        attempt_counts.append(total_attempts)
        
        if total_attempts > 0:
            subject_averages.append(round(total_percentage / total_attempts, 2))
            success_rates.append(round((successful_attempts / total_attempts) * 100, 2))
        else:
            subject_averages.append(0)
            success_rates.append(0)

    return render_template('summary.html',
                         subject_names=subject_names,
                         quiz_counts=quiz_counts,
                         subject_averages=subject_averages,
                         attempt_counts=attempt_counts,
                         success_rates=success_rates) 

@admin.route('/admin/scores')
def scores():
    subjects = Subject.query.all()
    users = User.query.all()
    scores_data = {}
    
    for user in users:
        scores_data[user.id] = []
        scores = Score.query.filter_by(user_id=user.id).all()
        for score in scores:
            scores_data[user.id].append({
                'quiz_name': score.quiz.name,
                'subject_name': score.quiz.chapter.subject.name,
                'chapter_name': score.quiz.chapter.name,
                'score': score.total_scored,
                'total_questions': len(score.quiz.questions),
                'percentage': round((score.total_scored / len(score.quiz.questions)) * 100, 2),
                'timestamp': score.time_stamp_of_attempt
            })
    
    return render_template('admin_scores.html', users=users, scores_data=scores_data)