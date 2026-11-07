import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify

import db


def create_app(test_config=None):
    """Build the Flask app: config, database and routes."""
    load_dotenv()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE=os.path.join(app.root_path, "database.db"),
        SESSION_COOKIE_NAME="site_auth",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",  # ASP.NET cookie default
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_REFRESH_EACH_REQUEST=True,
        MAX_CONTENT_LENGTH=3 * 1024 * 1024,  # photos are 2 MB max; the rest is multipart overhead
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY environment variable is required.")

    app.teardown_appcontext(db.close_db)
    db.init_db(app)

    from routes import auth, checklists, departments, feedback, photos, standard_checks, users
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(departments.bp)
    app.register_blueprint(standard_checks.bp)
    app.register_blueprint(checklists.bp)
    app.register_blueprint(feedback.bp)
    app.register_blueprint(photos.bp)

    @app.errorhandler(413)
    def too_large(e):
        """JSON instead of Flask's HTML page when a request body is too big."""
        return jsonify(photos.TOO_BIG), 413

    @app.get("/")
    def root():
        """Health check, same text as the C# version."""
        return "Server is running"

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
