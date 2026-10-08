from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from app.main import main
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
    # Pass a display-only version (no question banks) to the template
    assessment_display = {
        k: {
            "label":   v["label"],
            "icon":    v["icon"],
            "color":   v["color"],
            "time":    v["time"],
        }
        for k, v in ASSESSMENT_TYPES.items()
    }
    return render_template("dashboard.html", title="Dashboard",
                           assessment_types=assessment_display)
