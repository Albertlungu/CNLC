"""
./backend/api/routes/verification.py

Verification-related API endpoints (reCAPTCHA, etc.)
"""

import os

from flask import Blueprint, Response, jsonify, make_response, request

from backend.core.verification import verify_recaptcha

verification_bp = Blueprint("verification", __name__, url_prefix="/api")


@verification_bp.route("/submit-form", methods=["POST"])
def submit_form() -> Response:
    token = request.form.get("g-recaptcha-response")
    user_ip = request.remote_addr

    success, message = verify_recaptcha(
        response_token=token,
        secret_key=os.environ.get("RECAPTCHA_SECRET_KEY"),
        user_ip=user_ip,
    )

    if success:
        resp = jsonify({"status": "success"})
        return make_response(resp, 200)
    else:
        resp = jsonify({"status": "error", "message": message})
        return make_response(resp, 403)
