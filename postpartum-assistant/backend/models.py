from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

# Initialize SQLAlchemy without binding to app
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))  # Added password field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Added created_at
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    postpartum_entries = db.relationship('PostpartumSupportHistory', backref='user', lazy=True)  # New relationship

    def __repr__(self):
        return f'<User {self.name}>'

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sentiment = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Added created_at
    
    def __repr__(self):
        return f'<Analysis {self.id} - {self.sentiment}>'

class PostpartumSupportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    sleep_hours = db.Column(db.Float)
    support_activities = db.Column(db.Text)  # JSON string of activities
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostpartumEntry {self.id} - Mood: {self.mood_score}>'