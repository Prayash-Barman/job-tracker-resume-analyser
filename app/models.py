from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum

db = SQLAlchemy()

class Status(enum.Enum):
    APPLIED = "Applied"
    OA = "Online Assessment"
    INTERVIEW = "Interview"
    REJECTED = "Rejected"
    OFFER = "Offer"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    applications = db.relationship('Application', backref='user', lazy=True)
    resume = db.relationship('Resume', uselist=False, backref='user')

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum(Status), default=Status.APPLIED)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    job_description = db.Column(db.Text)
    notes = db.Column(db.Text)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    skills = db.Column(db.Text)  # Stored as comma-separated or JSON
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
