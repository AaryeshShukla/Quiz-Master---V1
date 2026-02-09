from flask import Blueprint, render_template, redirect, request,url_for,flash,session

from models.models import User,Subject,Chapter,Quiz,Question,UserAttempt
from models.database import db
from sqlalchemy.sql import func

controllers_bp = Blueprint("controllers", __name__)  # Define Blueprint

def get_db_connection():
        import sqlite3
        conn = sqlite3.connect("instance/quiz_master.sqlite3")
        conn.row_factory = sqlite3.Row
        return conn

#Login 
@controllers_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["user"] = dict(user)  
            session["user_id"] = user["id"]  
            session["user_type"] = user["type"]  

            print("Session After Login:", session) 

            if user["type"] == "admin":
                
                return redirect(url_for("controllers.admin_dashboard"))
            return redirect(url_for("controllers.user_dashboard"))

        return "Invalid credentials. <a href='/'>Try again</a>"

    return render_template("login.html")

#Register
@controllers_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        fullname = request.form["fullname"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        conn = get_db_connection()
        existing_user = conn.execute("SELECT * FROM user WHERE username = ?", (username,)).fetchone()
        if existing_user:
            conn.close()
            return "User already exists"
        conn.execute(
            "INSERT INTO user (username, password, fullname, qualification, dob, type) VALUES (?, ?, ?, ?, ?, 'user')",
            (username, password, fullname, qualification, dob)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

#Logout
@controllers_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

#User_Dashboard
@controllers_bp.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('controllers.login')) 

    subjects = Subject.query.all()  
    chapters = []
    quizzes = []
    questions = []

    selected_subject = request.form.get('subject')
    selected_chapter = request.form.get('chapter')

    if selected_subject:
        chapters = Chapter.query.filter_by(subject_id=selected_subject).all()

    if selected_subject and selected_chapter:
        quizzes = Quiz.query.filter_by(subject_id=selected_subject, chapter_id=selected_chapter).all()
        for quiz in quizzes:
            questions.extend(Question.query.filter_by(quiz_id=quiz.id).all())
            quiz.num_questions = Question.query.filter_by(quiz_id=quiz.id).count() 

    return render_template(
        'user_dashboard.html', 
        subjects=subjects, 
        chapters=chapters, 
        quizzes=quizzes, 
        questions=questions,
        selected_subject=selected_subject,
        selected_chapter=selected_chapter
    )

#Summary for user
@controllers_bp.route('/summary')
def summary_user():
 
    # Fetch number of attempts per subject
    attempt_counts = db.session.query(
        Subject.name, func.count(UserAttempt.id)
    ).join(Quiz, Quiz.subject_id == Subject.id) \
     .join(UserAttempt, UserAttempt.quiz_id == Quiz.id) \
     .group_by(Subject.name).all()

    attempts_subjects = [row[0] for row in attempt_counts]
    attempts = [row[1] for row in attempt_counts]

    return render_template('summary_user.html', 
                           
                           attempts_subjects=attempts_subjects, attempts=attempts)

#Starting the quiz
@controllers_bp.route("/start_quiz/<int:quiz_id>")
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("start_quiz.html", quiz=quiz, questions=questions)

#Sumbit form function for Start Quiz
@controllers_bp.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    score = 0
    for question in questions:
        selected_answer = request.form.get(f'question_{question.id}')
        if selected_answer is None:
            continue  # Skip unanswered questions
        if selected_answer.strip().upper() == question.correct_answer.strip().upper():
            score += 1

    user_id = session.get('user_id')
    # Store user attempt
    user_attempt = UserAttempt(user_id=user_id, quiz_id=quiz_id, score=score)  
    db.session.add(user_attempt)
    db.session.commit()

    return f"""
    <p>Quiz submitted! Your score: {score}</p>
    <a href="{url_for('controllers.user_dashboard')}" style="display: inline-block; padding: 10px 20px; 
       background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
        Go to Dashboard
    </a>
"""

#Viewing the quiz
@controllers_bp.route('/view_quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)  
    
    # Fetch related subject and chapter
    subject = Subject.query.get(quiz.subject_id)
    chapter = Chapter.query.get(quiz.chapter_id)

    return render_template('view_quiz.html', quiz=quiz, subject=subject, chapter=chapter)

@controllers_bp.route('/scores')
def scores():
    user_id = session.get('user_id')
  
    attempts = (
    db.session.query(UserAttempt, Quiz, Subject, Chapter)
    .join(Quiz, UserAttempt.quiz_id == Quiz.id)
    .join(Subject, Quiz.subject_id == Subject.id)
    .join(Chapter, Quiz.chapter_id == Chapter.id)
    .filter(UserAttempt.user_id == user_id)
    .order_by(UserAttempt.id.desc())
    .all()
      )

    scores_data = [
    {
        "quiz_title": attempt.Quiz.title, 
        "quiz_id": attempt.Quiz.title,
        "subject": attempt.Subject.name,  
        "chapter": attempt.Chapter.name,  
        "score": attempt.UserAttempt.score,
    }
    for attempt in attempts
    ]
    return render_template('score.html', scores=scores_data)

#admin_dashboard
@controllers_bp.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'POST':
        if 'subject_name' in request.form:  
            subject_name = request.form.get('subject_name').strip()
            if subject_name:
                existing_subject = Subject.query.filter_by(name=subject_name).first()
                if not existing_subject:
                    new_subject = Subject(name=subject_name)
                    db.session.add(new_subject)
                    db.session.commit()
                    flash('Subject added successfully!', 'success')
                else:
                    flash('Subject already exists!', 'danger')

        elif 'chapter_name' in request.form:  
            chapter_name = request.form.get('chapter_name').strip()
            subject_id = request.form.get('subject_id')
            if chapter_name and subject_id:
                new_chapter = Chapter(name=chapter_name, subject_id=subject_id)
                db.session.add(new_chapter)
                db.session.commit()
                flash('Chapter added successfully!', 'success')

        return redirect(url_for('controllers.admin_dashboard'))  

    subjects = Subject.query.all()

    subjects_with_chapters = [
        {
            'id': subject.id,
            'name': subject.name,
            'chapters': Chapter.query.filter_by(subject_id=subject.id).all()
        }
        for subject in subjects
    ]

    return render_template('admin_dashboard.html', subjects=subjects_with_chapters)


@controllers_bp.route('/users')
def user_management():
    users = User.query.all()
    return render_template('admin_user_management.html', users=users)

@controllers_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    UserAttempt.query.filter_by(user_id=user.id).delete()  # Delete attempts first
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    
    return redirect(url_for('controllers.user_management'))

@controllers_bp.route('/users/make_admin/<int:user_id>', methods=['POST'])
def make_admin(user_id):

    user = User.query.get_or_404(user_id)
    user.type = "admin"
    db.session.commit()
    flash(f"{user.username} is now an admin!", "success")

    return redirect(url_for('controllers.user_management'))


#Summary_admin
@controllers_bp.route('/admin/summary')
def summary_admin():
    # Fetch all subjects
    subjects = db.session.query(Subject).all()
    subject_names = [subject.name for subject in subjects]

    # Bar Chart - Average score of top users per subject
    avg_scores = []
    for subject in subjects:
        top_score = (
            db.session.query(db.func.avg(UserAttempt.score))
            .join(Quiz, UserAttempt.quiz_id == Quiz.id)
            .filter(Quiz.subject_id == subject.id)
            .group_by(UserAttempt.user_id)
            .order_by(db.func.avg(UserAttempt.score).desc())
            .limit(1)
            .scalar()
        )
        avg_scores.append(top_score if top_score else 0)  # Handle None values

    # Pie Chart - Number of quizzes per subject
    quiz_counts = [
        db.session.query(Quiz).filter(Quiz.subject_id == subject.id).count()
        for subject in subjects
    ]

    return render_template(
        'summary_admin.html',
        subjects=subject_names,
        avg_scores=avg_scores,
        quiz_counts=quiz_counts
    )




# Edit Chapter
@controllers_bp.route('/admin/edit_chapter/<int:chapter_id>', methods=['POST'])
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    new_name = request.form.get('new_chapter_name', '').strip()

    if new_name:
        chapter.name = new_name
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
    else:
        flash('Chapter name cannot be empty!', 'danger')

    return redirect(url_for('controllers.admin_dashboard'))


# **Delete Chapter**
@controllers_bp.route('/admin/delete_chapter/<int:chapter_id>', methods=['POST'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')

    return redirect(url_for('controllers.admin_dashboard'))

#EDIT SUBJECT
@controllers_bp.route('/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    new_name = request.form.get('new_subject_name')
    subject = Subject.query.get_or_404(subject_id)
    subject.name = new_name
    db.session.commit()
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('controllers.admin_dashboard'))

#delete_subject
@controllers_bp.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    quizzes = Quiz.query.filter_by(subject_id=subject.id).all()

    for quiz in quizzes:
        UserAttempt.query.filter_by(quiz_id=quiz.id).delete()

        Question.query.filter_by(quiz_id=quiz.id).delete()

        db.session.delete(quiz)

    # Delete all chapters under the subject
    Chapter.query.filter_by(subject_id=subject.id).delete()

    # Delete the subject itself
    db.session.delete(subject)
    db.session.commit()

    flash(f'Subject "{subject.name}" and its chapters deleted successfully!', 'success')
    return redirect(url_for('controllers.admin_dashboard'))

#View Quizzes for admin
@controllers_bp.route('/admin/view_quizzes_admin/<int:subject_id>/<int:chapter_id>', methods=['GET', 'POST'])
def view_quizzes_admin(chapter_id,subject_id): 
    # Fetch subject and chapter details
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Fetch quizzes for the selected subject and chapter
    quizzes = Quiz.query.filter_by(subject_id=subject_id, chapter_id=chapter_id).all()

    return render_template('view_quizes_admin.html', subject=subject, chapter=chapter, quizzes=quizzes)

#View Questions Admin (Edit and deletes questions)
@controllers_bp.route('/admin/quiz/<int:quiz_id>/questions', methods=['GET', 'POST'])
def view_questions_admin(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        action = request.form.get('action')
        question_id = request.form.get('question_id')

        if action == 'save':
            question = Question.query.get_or_404(question_id)
            question.text = request.form.get('text')
            question.option_a = request.form.get('option_a')
            question.option_b = request.form.get('option_b')
            question.option_c = request.form.get('option_c')
            question.option_d = request.form.get('option_d')
            question.correct_answer = request.form.get('correct_answer')

            db.session.commit()
            flash("Question updated successfully!", "success")

        elif action == 'delete':
            question = Question.query.get_or_404(question_id)
            db.session.delete(question)
            db.session.commit()
            flash("Question deleted successfully!", "danger")

        return redirect(url_for('controllers.view_questions_admin', quiz_id=quiz_id))

    return render_template('view_questions_admin.html', quiz=quiz, questions=questions)
   
#Add New Question
@controllers_bp.route('/admin/quiz/<int:quiz_id>/add-question', methods=['GET', 'POST'])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question_text = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['answer'] 

        new_question = Question(
            quiz_id=quiz_id,
            text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer
        )

        db.session.add(new_question)
        quiz.num_questions += 1

        db.session.commit()
        flash('Question added successfully!', 'success')

        return redirect(url_for('controllers.view_quizzes_admin', subject_id=quiz.subject_id, chapter_id=quiz.chapter_id))


    return render_template('add_question.html', quiz=quiz)

#Delete the Quiz
@controllers_bp.route('/admin/quiz/delete/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    Question.query.filter_by(quiz_id=quiz.id).delete()
    db.session.delete(quiz)
    db.session.commit()
    
    flash("Quiz deleted successfully!", "success")
    return redirect(url_for('controllers.view_quizzes_admin', chapter_id=quiz.chapter_id, subject_id=quiz.subject_id)) 

#Creating Quiz
@controllers_bp.route('/admin/quiz/new', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'POST':
        chapter_id = request.form['chapter_id']
        chapter = Chapter.query.get_or_404(chapter_id)  
        admin_username = request.form['admin_username']  
        admin = User.query.filter_by(username=admin_username).first()  
        new_quiz = Quiz(
        title=request.form['title'],
        subject_id=chapter.subject_id,
        chapter_id=chapter_id,
        admin_id=admin.id,
        num_questions=request.form['num_questions'],
        duration=request.form['duration']
        )
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz created successfully!", "success")
        return redirect(url_for('controllers.view_quizzes_admin', chapter_id=chapter_id,subject_id=chapter.subject_id))
    
    chapter_id = request.args.get('chapter_id')
    return render_template('create_quiz.html', chapter_id=chapter_id)


