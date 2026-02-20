from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    phone = db.Column(db.String(20))

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    symptoms = db.Column(db.Text)
    diabetes = db.Column(db.Float)
    heart = db.Column(db.Float)
    kidney = db.Column(db.Float)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
