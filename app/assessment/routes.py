from flask import render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user

from app.assessment import assessment

# ── Allowed assessment types (server-side whitelist) ─────────────────────
ASSESSMENT_TYPES = {
    "cognitive":    {"label": "Cognitive Skills",       "icon": "🧠", "questions": 10, "time": "~10 min"},
    "personality":  {"label": "Personality Profile",    "icon": "🌟", "questions": 10, "time": "~8 min"},
    "emotional":    {"label": "Emotional Intelligence", "icon": "❤️", "questions": 10, "time": "~12 min"},
    "leadership":   {"label": "Leadership Aptitude",    "icon": "🧑‍💼", "questions": 10, "time": "~15 min"},
    "stress":       {"label": "Stress & Wellbeing",     "icon": "🧘", "questions": 10, "time": "~6 min"},
    "career":       {"label": "Career Aptitude",        "icon": "💼", "questions": 10, "time": "~10 min"},
}


# ── Assessment Selection ──────────────────────────────────────────────────
@assessment.route("/select", methods=["GET", "POST"])
@login_required
def select():
    if request.method == "POST":
        a_type = request.form.get("assessment_type", "").strip()
        if a_type not in ASSESSMENT_TYPES:
            flash("Please select a valid assessment type.", "warning")
            return redirect(url_for("assessment.select"))
        session["assessment_type"]  = a_type
        session["assessment_label"] = ASSESSMENT_TYPES[a_type]["label"]
        session.pop("personal_info", None)   # clear any stale data
        session.pop("answers", None)
        return redirect(url_for("assessment.personal_info"))
    return render_template("assessment/select.html", title="Choose Assessment",
                           assessment_types=ASSESSMENT_TYPES)


# ── Personal Information ──────────────────────────────────────────────────
@assessment.route("/personal-info", methods=["GET", "POST"])
@login_required
def personal_info():
    # Guard: must have selected an assessment first
    if not session.get("assessment_type"):
        flash("Please select an assessment first.", "warning")
        return redirect(url_for("assessment.select"))

    if request.method == "POST":
        session["personal_info"] = {
            "first_name":  request.form.get("first_name",  "").strip(),
            "last_name":   request.form.get("last_name",   "").strip(),
            "age_group":   request.form.get("age_group",   ""),
            "gender":      request.form.get("gender",      ""),
            "education":   request.form.get("education",   ""),
            "occupation":  request.form.get("occupation",  "").strip(),
            "goal":        request.form.get("goal",        ""),
            "notes":       request.form.get("notes",       "").strip(),
        }
        return redirect(url_for("assessment.questionnaire"))

    return render_template("assessment/personal_info.html",
                           title="Personal Information",
                           assessment_label=session.get("assessment_label", "Assessment"))


# ── Questionnaire ─────────────────────────────────────────────────────────
@assessment.route("/questionnaire", methods=["GET", "POST"])
@login_required
def questionnaire():
    if not session.get("assessment_type"):
        flash("Please start from the beginning.", "warning")
        return redirect(url_for("assessment.select"))

    if request.method == "POST":
        answers = {}
        for i in range(1, 11):
            val = request.form.get(f"q{i}")
            if val:
                answers[f"q{i}"] = val   # store as string label, not index
        session["answers"] = answers
        answered = len(answers)
        if answered < 10:
            flash(f"Please answer all questions. You answered {answered} of 10.", "warning")
            return redirect(url_for("assessment.questionnaire"))
        return redirect(url_for("assessment.review"))

    # Restore saved answers for display
    saved = session.get("answers", {})
    return render_template("assessment/questionnaire.html",
                           title="Questionnaire",
                           saved_answers=saved,
                           assessment_label=session.get("assessment_label", "Assessment"))


# ── Progress Tracking ─────────────────────────────────────────────────────
@assessment.route("/progress")
@login_required
def progress():
    return render_template("assessment/progress.html", title="Progress Tracking")


# ── Review Answers ────────────────────────────────────────────────────────
@assessment.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if not session.get("answers"):
        flash("No answers found. Please complete the questionnaire first.", "warning")
        return redirect(url_for("assessment.questionnaire"))

    if request.method == "POST":
        # Confirmation via form, not a bare GET link
        return redirect(url_for("assessment.processing"))

    answers       = session.get("answers", {})
    p_info        = session.get("personal_info", {})
    a_type        = session.get("assessment_type", "general")
    a_label       = session.get("assessment_label", "Assessment")
    total_q       = 10
    answered_count = len(answers)

    return render_template(
        "assessment/review.html",
        title="Review Answers",
        answers=answers,
        personal_info=p_info,
        assessment_type=a_type,
        assessment_label=a_label,
        total_q=total_q,
        answered_count=answered_count,
    )


# ── Processing ────────────────────────────────────────────────────────────
@assessment.route("/processing")
@login_required
def processing():
    if not session.get("answers"):
        return redirect(url_for("assessment.select"))
    return render_template("assessment/processing.html", title="Processing")


# ── Result ────────────────────────────────────────────────────────────────
@assessment.route("/result")
@login_required
def result():
    answers = session.get("answers", {})
    a_type  = session.get("assessment_type", "general")
    a_label = session.get("assessment_label", "Assessment")
    a_info  = ASSESSMENT_TYPES.get(a_type, {"label": a_label, "icon": "📋"})

    # Score: each q answered 1–5; 1=best. Convert to 0–100.
    if answers:
        vals = []
        for v in answers.values():
            try:
                vals.append(int(v))
            except (ValueError, TypeError):
                # Text answers score as 3 (mid)
                vals.append(3)
        raw   = sum(vals) / len(vals)
        score = round(((5 - raw) / 4) * 100)
    else:
        score = 75  # fallback

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Plain-language band
    if score >= 85:
        band, band_color = "High", "success"
    elif score >= 65:
        band, band_color = "Moderate", "warning"
    else:
        band, band_color = "Low", "danger"

    return render_template(
        "assessment/result.html",
        title="Your Results",
        score=score,
        band=band,
        band_color=band_color,
        assessment_type=a_type,
        assessment_label=a_label,
        assessment_info=a_info,
        answers=answers,
    )


# ── Guidance / Recommendations ────────────────────────────────────────────
@assessment.route("/recommendations")
@login_required
def recommendations():
    a_type  = session.get("assessment_type", "general")
    a_label = session.get("assessment_label", "Assessment")
    return render_template(
        "assessment/recommendations.html",
        title="Guidance & Interpretation",
        assessment_type=a_type,
        assessment_label=a_label,
    )


# ── History ───────────────────────────────────────────────────────────────
@assessment.route("/history")
@login_required
def history():
    return render_template("assessment/history.html", title="Assessment History")


# ── Help / Information ────────────────────────────────────────────────────
@assessment.route("/help")
def help_page():
    return render_template("assessment/help.html", title="Help & Information")


# ── Delete stub (future DB implementation) ───────────────────────────────
@assessment.route("/delete/<int:assessment_id>", methods=["POST"])
@login_required
def delete_assessment(assessment_id):
    # Stub: in a full implementation this would soft-delete from DB
    flash("Assessment record deleted.", "success")
    return redirect(url_for("assessment.history"))
