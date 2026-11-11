from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from app.main import main
from app.models import AssessmentRecord
from app.assessment.routes import ASSESSMENT_TYPES


@main.route("/")
@main.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html", title="Welcome")


@main.route("/dashboard")
@login_required
def dashboard():
    # Real stats from DB
    records = (
        AssessmentRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(AssessmentRecord.completed_at.desc())
        .all()
    )
    total       = len(records)
    completed   = sum(1 for r in records if r.status == "completed")
    in_progress = sum(1 for r in records if r.status == "in_progress")
    recent      = records[:5]   # up to 5 most recent for the dashboard panel

    # Display-only version of assessment types (no question banks)
    assessment_display = {
        k: {
            "label":   v["label"],
            "icon":    v["icon"],
            "color":   v["color"],
            "time":    v["time"],
        }
        for k, v in ASSESSMENT_TYPES.items()
    }

    return render_template(
        "dashboard.html",
        title="Dashboard",
        assessment_types=assessment_display,
        total=total,
        completed=completed,
        in_progress=in_progress,
        recent=recent,
    )
