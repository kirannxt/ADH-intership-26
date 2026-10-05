from flask import Blueprint

assessment = Blueprint("assessment", __name__)

from app.assessment import routes  # noqa: F401, E402
