from flask import render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user

from app.assessment import assessment


# ── Assessment Selection ────────────────────────────────────────────────────
@assessment.route("/select", methods=["GET", "POST"])
@login_required
def select():
    if request.method == "POST":
        assessment_type = request.form.get("assessment_type", "").strip()
        if not assessment_type:
            flash("Please select an assessment type.", "warning")
            return redirect(url_for("assessment.select"))
        session["assessment_type"] = assessment_type
        return redirect(url_for("assessment.personal_info"))
    return render_template("assessment/select.html", title="Choose Assessment")


# ── Personal Information ────────────────────────────────────────────────────
@assessment.route("/personal-info", methods=["GET", "POST"])
@login_required
def personal_info():
    if request.method == "POST":
        session["personal_info"] = {
            "first_name":  request.form.get("first_name", "").strip(),
            "last_name":   request.form.get("last_name", "").strip(),
            "dob":         request.form.get("dob", ""),
            "gender":      request.form.get("gender", ""),
            "education":   request.form.get("education", ""),
            "occupation":  request.form.get("occupation", "").strip(),
            "goal":        request.form.get("goal", ""),
            "notes":       request.form.get("notes", "").strip(),
        }
        return redirect(url_for("assessment.questionnaire"))
    return render_template("assessment/personal_info.html", title="Personal Information")


# ── Questionnaire ───────────────────────────────────────────────────────────
@assessment.route("/questionnaire", methods=["GET", "POST"])
@login_required
def questionnaire():
    if request.method == "POST":
        answers = {}
        for i in range(1, 11):
            val = request.form.get(f"q{i}")
            if val:
                answers[f"q{i}"] = int(val)
        session["answers"] = answers
        if len(answers) < 10:
            flash("Please answer all questions before continuing.", "warning")
            return redirect(url_for("assessment.questionnaire"))
        return redirect(url_for("assessment.review"))
    return render_template("assessment/questionnaire.html", title="Questionnaire")


# ── Progress Tracking ───────────────────────────────────────────────────────
@assessment.route("/progress")
@login_required
def progress():
    return render_template("assessment/progress.html", title="Progress Tracking")


# ── Review Answers ──────────────────────────────────────────────────────────
@assessment.route("/review", methods=["GET", "POST"])
@login_required
def review():
    if request.method == "POST":
        return redirect(url_for("assessment.processing"))
    answers  = session.get("answers", {})
    p_info   = session.get("personal_info", {})
    a_type   = session.get("assessment_type", "general")
    return render_template(
        "assessment/review.html",
        title="Review Answers",
        answers=answers,
        personal_info=p_info,
        assessment_type=a_type,
    )


# ── Processing ──────────────────────────────────────────────────────────────
@assessment.route("/processing")
@login_required
def processing():
    return render_template("assessment/processing.html", title="Processing")


# ── Result ──────────────────────────────────────────────────────────────────
@assessment.route("/result")
@login_required
def result():
    answers    = session.get("answers", {})
    a_type     = session.get("assessment_type", "general")
    # Simple demo score: mean of answers (scale 1-5) → percent
    if answers:
        raw   = sum(answers.values()) / len(answers)
        score = round(((5 - raw) / 4) * 100)   # higher answer index = lower score for demo
    else:
        score = 84  # fallback demo value
    return render_template(
        "assessment/result.html",
        title="Your Results",
        score=score,
        assessment_type=a_type,
    )


# ── Recommendations ─────────────────────────────────────────────────────────
@assessment.route("/recommendations")
@login_required
def recommendations():
    a_type = session.get("assessment_type", "general")
    return render_template(
        "assessment/recommendations.html",
        title="Recommendations",
        assessment_type=a_type,
    )


# ── History ─────────────────────────────────────────────────────────────────
@assessment.route("/history")
@login_required
def history():
    return render_template("assessment/history.html", title="Assessment History")
