import os
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# --- Extensions ---
db = SQLAlchemy()
bcrypt = Bcrypt()


# --- App Factory ---
def create_app():
    app = Flask(__name__)

    # In real prod you'll use a strong secret via environment variable
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # SQLite for now; later we can switch to Postgres
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///imli_marketplace.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    bcrypt.init_app(app)

    return app


# --- Models ---

class User(db.Model):
    """
    Base user model. Lawyers and Applicants both live here, with role-based profiles.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # "lawyer" or "applicant" (later we can add "admin")
    role = db.Column(db.String(50), nullable=False)

    # basic info
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    # verification status for the account as a whole
    is_verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    lawyer_profile = db.relationship("LawyerProfile", uselist=False, back_populates="user")
    applicant_profile = db.relationship("ApplicantProfile", uselist=False, back_populates="user")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class LawyerProfile(db.Model):
    """
    Lawyer-specific data (bar details, specializations, rates, etc.).
    """
    __tablename__ = "lawyer_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="lawyer_profile")

    # Bar & identity
    bar_number = db.Column(db.String(100), nullable=True)
    bar_state = db.Column(db.String(100), nullable=True)
    law_firm_name = db.Column(db.String(255), nullable=True)

    # Practice details
    primary_visa_focus = db.Column(db.String(50), nullable=True)  # e.g. "O-1", "EB-2 NIW", "F-1"
    other_visa_types = db.Column(db.String(255), nullable=True)   # comma-separated for MVP

    years_experience = db.Column(db.Integer, nullable=True)
    languages = db.Column(db.String(255), nullable=True)  # e.g. "English, Spanish, Hindi"

    # Rates – MVP simple; later we can normalize into a separate table
    consultation_fee_usd = db.Column(db.Integer, nullable=True)  # in cents later; simple int USD now
    hourly_rate_usd = db.Column(db.Integer, nullable=True)

    # Location
    office_city = db.Column(db.String(100), nullable=True)
    office_state = db.Column(db.String(100), nullable=True)
    office_country = db.Column(db.String(100), nullable=True, default="United States")

    # Profile
    bio = db.Column(db.Text, nullable=True)
    is_accepting_new_clients = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class ApplicantProfile(db.Model):
    """
    Applicant-specific data (country, visa interest, background).
    """
    __tablename__ = "applicant_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="applicant_profile")

    country_of_citizenship = db.Column(db.String(100), nullable=True)
    current_country_of_residence = db.Column(db.String(100), nullable=True)

    # What they think they want (we can refine with AI later)
    intended_visa_type = db.Column(db.String(50), nullable=True)  # e.g. "F-1", "H-1B", "O-1"
    target_start_date = db.Column(db.String(50), nullable=True)   # keep simple for MVP

    # Optional quick background fields
    education_level = db.Column(db.String(100), nullable=True)    # e.g. "Bachelor's", "PhD"
    field_of_study = db.Column(db.String(255), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# --- DB init helper (run this once to create tables) ---

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ imli_marketplace.db database created with core tables.")


if __name__ == "__main__":
    # For Day 1, running this file will create the DB and exit.
    init_db()
