from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
import PyPDF2

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db = SQLAlchemy(app)

def extract_text(pdf_path):

    text = ""

    with open(pdf_path, "rb") as file:

        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:

            text += page.extract_text()

    return text

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    jobs = db.relationship(
        'JobApplication',
        backref='owner',
        lazy=True
    )
class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

    status = db.Column(db.String(50), nullable=False)

    date_applied = db.Column(db.String(50))

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already registered"

        user = User(
            username=username,
            email=email,
            password=password
        )
        print("Registering:", username, email)
        db.session.add(user)
        db.session.commit()
        print("User saved successfully")

        flash("Registration successful")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/add_job", methods=["GET", "POST"])
@login_required
def add_job():

    if request.method == "POST":

        company = request.form["company"]
        role = request.form["role"]
        status = request.form["status"]
        date_applied = request.form["date"]

        job = JobApplication(
            company=company,
            role=role,
            status=status,
            date_applied=date_applied,
            user_id=current_user.id
        )

        db.session.add(job)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_job.html")


@app.route("/delete_job/<int:id>")
@login_required
def delete_job(id):

    job = JobApplication.query.get_or_404(id)

    if job.user_id != current_user.id:
        return "Unauthorized"

    db.session.delete(job)
    db.session.commit()

    return redirect(url_for("dashboard"))

@app.route("/edit_job/<int:id>", methods=["GET", "POST"])
@login_required
def edit_job(id):

    job = JobApplication.query.get_or_404(id)

    if job.user_id != current_user.id:
        return "Unauthorized"

    if request.method == "POST":

        job.status = request.form["status"]

        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_job.html",
        job=job
    )

@app.route("/dashboard")
@login_required
def dashboard():

    jobs = JobApplication.query.filter_by(
        user_id=current_user.id
    ).all()

    total_jobs = len(jobs)

    applied = len(
        [job for job in jobs
         if job.status == "Applied"]
    )

    oa = len(
        [job for job in jobs
         if job.status == "OA"]
    )

    interviews = len(
        [job for job in jobs
         if job.status == "Interview"]
    )

    offers = len(
        [job for job in jobs
         if job.status == "Offer"]
    )

    rejected = len(
        [job for job in jobs
         if job.status == "Rejected"]
    )

    return render_template(
        "dashboard.html",
        username=current_user.username,
        jobs=jobs,
        total_jobs=total_jobs,
        applied=applied,
        oa=oa,
        interviews=interviews,
        offers=offers,
        rejected=rejected
    )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume():

    if request.method == "POST":

        file = request.files["resume"]

        if file:

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )

            file.save(filepath)

            return redirect(
                url_for(
                    "analyze_resume",
                    filename=file.filename
                )
            )

    return render_template("resume.html")

@app.route("/analyze/<filename>", methods=["GET", "POST"])
@login_required
def analyze_resume(filename):

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume_text = extract_text(filepath)

    score = None
    matched = []
    missing = []

    if request.method == "POST":

        job_description = request.form["job_description"]

        keywords = [
            "python",
            "flask",
            "sql",
            "git",
            "docker",
            "aws",
            "javascript",
            "html",
            "css"
        ]

        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()

        required_keywords = []

        for keyword in keywords:

            if keyword in jd_lower:
                required_keywords.append(keyword)

        for keyword in required_keywords:

            if keyword in resume_lower:
                matched.append(keyword)
            else:
                missing.append(keyword)

        if required_keywords:
            score = int(
                len(matched) /
                len(required_keywords) * 100
            )

    return render_template(
        "analyze.html",
        resume_text=resume_text[:3000],
        score=score,
        matched=matched,
        missing=missing
    )


if __name__ == "__main__":

    app.run(debug=True)
