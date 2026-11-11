import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify

import db


def create_app(test_config=None):
    """Build the Flask app: config, database and routes."""
    load_dotenv()
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wwwroot"),
                static_url_path="")  # the pages and /api share one address, so the login cookie works
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

    from routes import (auth, checklists, departments, feedback, links, phones, photos, pop_departments, pop_links,
                        pop_phones, pops, standard_checks, tools, user_departments, users)
    for module in (auth, users, departments, user_departments, pops, pop_departments, standard_checks, checklists,
                   feedback, photos, links, pop_links, phones, pop_phones, tools):
        app.register_blueprint(module.bp, url_prefix="/api")

    @app.errorhandler(413)
    def too_large(e):
        """JSON instead of Flask's HTML page when a request body is too big."""
        return jsonify(photos.TOO_BIG), 413

    @app.get("/")
    def root():
        """The portal's home page."""
        return app.send_static_file("index.html")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
