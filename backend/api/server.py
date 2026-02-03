"""
./backend/api/server.py

Entry point for web API. The main file that ties everything together.
"""

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

load_dotenv()

from backend.api.routes import (
    auth_bp,
    bookmarks_bp,
    businesses_bp,
    deals_bp,
    friends_bp,
    notifications_bp,
    reservations_bp,
    reviews_bp,
    saved_bp,
    sessions_bp,
    trending_bp,
    users_bp,
    recommendations_bp,
    verification_bp,
)
from config.config import PROJECT_ROOT

app = Flask(__name__)

CORS(app, origins="*")

app.config["JSON_SORT_KEYS"] = False
app.config["JSON_AS_ASCII"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

UPLOAD_FOLDER = PROJECT_ROOT / "data" / "uploads"


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded files (review photos)"""
    return send_from_directory(str(UPLOAD_FOLDER), filename)


# ================== Error Handling ================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with a JSON response (resource not found)"""
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors with a JSON response (Pydantic validation)"""
    return jsonify({"error": "Invalid request."}), 400


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors with a JSON response (internal server error)"""
    return jsonify({"error": "Internal server error."}), 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors with JSON response (access forbidden)"""
    return jsonify({"error": "Forbidden"}), 403


# ================== Health Check ================


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check to ensure that server is running"""
    return jsonify({"status": "healthy"}), 200


# ================== Register Blueprints ================

app.register_blueprint(auth_bp)
app.register_blueprint(bookmarks_bp)
app.register_blueprint(businesses_bp)
app.register_blueprint(deals_bp)
app.register_blueprint(friends_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(saved_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(trending_bp)
app.register_blueprint(users_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(recommendations_bp)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
