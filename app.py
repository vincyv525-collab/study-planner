from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
import os

app.config['UPLOAD_FOLDER'] = 'static/uploads/pdfs'

@app.route("/")
def index():
    return redirect(url_for("login"))

app.config['SECRET_KEY'] = 'studybloomsecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# USER MODEL
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tasks = db.relationship('Task', backref='user', lazy=True)
    
    avatar = db.Column(
        db.String(100),
        default="sakura.png"
    )
    theme = db.Column(
    db.String(50),
    default="pink"
)


# TASK MODEL
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(100))
    priority = db.Column(db.String(20))
    deadline = db.Column(db.String(50))

    completed = db.Column(db.Boolean, default=False)
    streak = db.Column(db.Integer, default=0)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    content = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
class PomodoroSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    duration = db.Column(db.Integer)  # minutes (25 or 5)
    type = db.Column(db.String(20))   # focus / break

    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class SemesterEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(100))

    event_type = db.Column(db.String(50))

    event_date = db.Column(db.String(50))

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

class Journal(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200)
    )

    content = db.Column(
        db.Text
    )

    date = db.Column(
        db.String(50)
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    with app.app_context():
    db.create_all()
    
@app.route("/add_task", methods=["POST"])
@login_required
def add_task():

    task = Task(
        title=request.form["title"],
        subject=request.form["subject"],
        priority=request.form["priority"],
        deadline=request.form["deadline"],
        user_id=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get(id)

    db.session.delete(task)

    db.session.commit()

    return redirect(url_for("dashboard"))
@app.route("/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get(id)

    task.completed = True

    db.session.commit()

    return redirect(url_for("dashboard"))
    
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(
            request.form["password"]
        )

        user = User(
            username=username,
            email=email,
            password=password,
            avatar=request.form["avatar"]
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username).first()

    if user is None:
        flash("User not found")
        return redirect(url_for("login"))

    if check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for("dashboard"))
    else:
        flash("Wrong password")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()

    materials = StudyMaterial.query.filter_by(
        user_id=current_user.id
    ).all()

    notes = Note.query.filter_by(
        user_id=current_user.id
    ).all()

    events = SemesterEvent.query.filter_by(
        user_id=current_user.id
    ).all()

    journals = Journal.query.filter_by(
    user_id=current_user.id
    ).all()

    from datetime import datetime

    reminders = []

    today = datetime.today().date()

    for event in events:

        try:
            event_date = datetime.strptime(
                event.event_date,
                "%Y-%m-%d"
            ).date()

            days_left = (event_date - today).days

            if days_left == 0:
                reminders.append(
                    f"🎓 {event.title} is today!"
                )

            elif days_left <= 3:
                reminders.append(
                    f"⚠️ {event.title} in {days_left} day(s)"
                )

        except:
            pass

    high_tasks = Task.query.filter_by(
        user_id=current_user.id,
        completed=False,
        priority="High"
    ).all()

    if len(high_tasks) > 0:
        reminders.append(
            f"🔥 {len(high_tasks)} high-priority task(s) pending"
        )   

    total = len(tasks)

    completed = len(
        [task for task in tasks if task.completed]
    )

    pending = total - completed

    progress = int(
        (completed / total) * 100
    ) if total > 0 else 0

    quotes = [
        "Small progress is still progress 🌸",
        "You can do hard things 💖",
        "One task at a time ✨",
        "Future you will thank you 🌷",
        "Consistency beats perfection 🌙"
    ]

    quote = random.choice(quotes)

    badge = "🌱 Beginner"

    if progress >= 10:
        badge = "🌸 Productive"

    if progress >= 25:
        badge = "🏆 Study Queen"

    if progress >= 50:
        badge = "👑 Academic Legend"

    return render_template(
        "dashboard.html",
        user=current_user,
        tasks=tasks,
        materials=materials,
        notes=notes,
        events=events,
        reminders=reminders,
        journals=journals,
        total=total,
        completed=completed,
        pending=pending,
        progress=progress,
        quote=quote,
        badge=badge
    )
@app.route(
"/change_theme",
methods=["POST"]
)
@login_required
def change_theme():

    current_user.theme = (
        request.form["theme"]
    )

    db.session.commit()

    return redirect(
        url_for("dashboard"))
    if not current_user.is_authenticated:
     return redirect(url_for("login"))

    
import os
from werkzeug.utils import secure_filename

app.config['UPLOAD_FOLDER'] = 'static/uploads/pdfs'


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("login")
    )

from werkzeug.utils import secure_filename

@app.route("/upload_material", methods=["POST"])
@login_required
def upload_material_pdf():

    file = request.files["pdf"]
    title = request.form["title"]
    subject = request.form["subject"]

    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("dashboard"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(filepath)

    material = StudyMaterial(
        title=title,
        subject=subject,
        filename=filename,
        user_id=current_user.id
    )

    db.session.add(material)
    db.session.commit()

    flash("PDF uploaded successfully!")
    return redirect(url_for("dashboard"))

@app.route("/add_note", methods=["POST"])
@login_required
def add_note():

    note = Note(
        title=request.form["title"],
        content=request.form["content"],
        user_id=current_user.id
    )

    db.session.add(note)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/add_journal", methods=["POST"])
@login_required
def add_journal():

    journal = Journal(
        title=request.form["title"],
        content=request.form["content"],
        date=request.form["date"],
        user_id=current_user.id
    )

    db.session.add(journal)
    db.session.commit()

    return redirect(
        url_for("dashboard")
    )


@app.route("/add_event", methods=["POST"])
@login_required
def add_event():

    event = SemesterEvent(
        title=request.form["title"],
        subject=request.form["subject"],
        event_type=request.form["event_type"],
        event_date=request.form["event_date"],
        user_id=current_user.id
    )

    db.session.add(event)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/notes")
@login_required
def notes_page():

    notes = Note.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "notes.html",
        notes=notes
    )
@app.route("/journal")
@login_required
def journal():

    journals = Journal.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "journal.html",
        journals=journals
    )
@app.route("/semester")
@login_required
def semester():

    events = SemesterEvent.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "semester.html",
        events=events
    )
@app.route("/materials")
@login_required
def materials():

    materials = StudyMaterial.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "materials.html",
        materials=materials
    )
@app.route("/pomodoro")
@login_required
def pomodoro():

    return render_template(
        "pomodoro.html"
    )


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
