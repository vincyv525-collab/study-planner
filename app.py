from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)

# ✅ SECRET
app.config['SECRET_KEY'] = 'studybloomsecret'

# ✅ IMPORTANT: Railway DB Fix
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Upload folder fix
UPLOAD_FOLDER = 'static/uploads/pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# ✅ Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ===================== MODELS ===================== #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    avatar = db.Column(db.String(100), default="sakura.png")
    theme = db.Column(db.String(50), default="pink")

    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(100))
    priority = db.Column(db.String(20))
    deadline = db.Column(db.String(50))

    completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(100))
    filename = db.Column(db.String(200))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    content = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class SemesterEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    subject = db.Column(db.String(100))
    event_type = db.Column(db.String(50))
    event_date = db.Column(db.String(50))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    date = db.Column(db.String(50))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# ✅ Create DB
with app.app_context():
    db.create_all()

# ===================== LOGIN ===================== #

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===================== ROUTES ===================== #

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # ⚠️ Fix duplicate users crash
        existing_user = User.query.filter_by(username=request.form["username"]).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"])
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created!")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        user = User.query.filter_by(username=request.form["username"]).first()

        if not user:
            flash("User not found")
            return redirect(url_for("login"))

        if check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Wrong password")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    tasks = Task.query.filter_by(user_id=current_user.id).all()
    events = SemesterEvent.query.filter_by(user_id=current_user.id).all()

    total = len(tasks)
    completed = len([t for t in tasks if t.completed])

    progress = int((completed / total) * 100) if total > 0 else 0

    quote = random.choice([
        "You got this 💖",
        "Stay consistent 🌸",
        "Focus mode ON 🔥"
    ])

    return render_template(
        "dashboard.html",
        tasks=tasks,
        events=events,
        progress=progress,
        quote=quote
    )

# ===================== ACTIONS ===================== #

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

    print("✅ Event Added:", event.title)  # DEBUG

    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ===================== RUN ===================== #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
