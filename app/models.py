import json
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessments = db.relationship("AssessmentRecord", backref="user",
                                  lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class AssessmentRecord(db.Model):
    """Persisted result of a completed assessment."""
    __tablename__ = "assessment_records"

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Assessment metadata
    assessment_type  = db.Column(db.String(32),  nullable=False)
    assessment_label = db.Column(db.String(128), nullable=False)

    # Scores
    raw_score   = db.Column(db.Integer,  nullable=False, default=0)
    pct_score   = db.Column(db.Integer,  nullable=False, default=0)
    band        = db.Column(db.String(64),  nullable=False, default="")
    band_color  = db.Column(db.String(32),  nullable=False, default="primary")

    # Status: "completed" or "in_progress"
    status = db.Column(db.String(16), nullable=False, default="completed")

    # Duration in seconds (set when submitting)
    duration_seconds = db.Column(db.Integer, nullable=True)

    # JSON blobs for answers and personal_info
    answers_json      = db.Column(db.Text, nullable=True)
    personal_info_json = db.Column(db.Text, nullable=True)

    completed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # -- Convenience helpers -----------------------------------------------

    @property
    def answers(self):
        return json.loads(self.answers_json) if self.answers_json else {}

    @property
    def personal_info(self):
        return json.loads(self.personal_info_json) if self.personal_info_json else {}

    @property
    def duration_display(self):
        """Return a human-readable duration string like '4m 32s', or '—'."""
        if not self.duration_seconds:
            return "—"
        m, s = divmod(self.duration_seconds, 60)
        return f"{m}m {s}s" if m else f"{s}s"

    @property
    def score_display(self):
        return f"{self.pct_score}%"

    @property
    def icon(self):
        _icons = {
            "adhd":       "AD",
            "anxiety":    "AX",
            "depression": "DP",
            "stress":     "ST",
            "learning":   "LS",
            "eq":         "EQ",
            "asd":        "AS",
        }
        return _icons.get(self.assessment_type, "--")

    @property
    def color_bg(self):
        _colors = {
            "adhd":       "#ede9fe",
            "anxiety":    "#dbeafe",
            "depression": "#e0e7ff",
            "stress":     "#d1fae5",
            "learning":   "#fef3c7",
            "eq":         "#fee2e2",
            "asd":        "#ecfdf5",
        }
        return _colors.get(self.assessment_type, "#f3f4f6")

    @property
    def badge_class(self):
        if self.status == "completed":
            return "success"
        return "warning"

    def __repr__(self) -> str:
        return f"<AssessmentRecord {self.id} user={self.user_id} type={self.assessment_type}>"


class MLModel(db.Model):
    """
    Tracks metadata for a persisted per-user per-type ML model.
    The actual model binary is stored on disk at:
        instance/ml_models/<user_id>/<assessment_type>.pkl
    """
    __tablename__ = "ml_models"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"),
                                nullable=False, index=True)
    assessment_type = db.Column(db.String(32), nullable=False)
    algorithm       = db.Column(db.String(64), nullable=False, default="")
    n_samples       = db.Column(db.Integer,  nullable=False, default=0)
    n_features      = db.Column(db.Integer,  nullable=False, default=0)
    accuracy        = db.Column(db.Float,    nullable=True)   # CV accuracy 0–1
    trained_at      = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    model_path      = db.Column(db.String(256), nullable=False, default="")

    # Composite unique constraint — one model record per user per type
    __table_args__ = (
        db.UniqueConstraint("user_id", "assessment_type", name="uq_ml_user_type"),
    )

    @property
    def accuracy_pct(self) -> str:
        if self.accuracy is None:
            return "—"
        return f"{round(self.accuracy * 100)}%"

    @property
    def trained_ago(self) -> str:
        from datetime import datetime, timezone
        delta = datetime.utcnow() - self.trained_at
        days = delta.days
        if days == 0:
            mins = delta.seconds // 60
            return f"{mins}m ago" if mins > 1 else "just now"
        return f"{days}d ago"

    def __repr__(self) -> str:
        return (f"<MLModel user={self.user_id} type={self.assessment_type} "
                f"algo={self.algorithm} acc={self.accuracy_pct}>")


@login_manager.user_loader
def load_user(user_id: int):
    return User.query.get(int(user_id))
