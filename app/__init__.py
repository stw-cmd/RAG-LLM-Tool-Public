# app/__init__.py
import os
import logging
from datetime import datetime
from flask import Flask, render_template, url_for
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf

from .config     import Config
from .extensions import db, mail
from .utils      import setup_pandoc, initialize_nltk_resources

# Blueprints imports
from .auth.routes      import auth_bp
from .documents.routes import document_bp
from .queries.routes   import query_bp
from .admin.routes     import admin_bp

# Logging config
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configure Flask app
def create_app():
    # Determine directories
    here = os.path.dirname(__file__) 
    project_root = os.path.abspath(os.path.join(here, os.pardir)) 
    static_dir = os.path.join(project_root, 'static')             
    template_dir = os.path.join(here, 'templates')               
    # Debug output to verify paths
    print(f"[DEBUG] Flask static_folder set to: {static_dir}")
    print(f"[DEBUG] Flask template_folder set to: {template_dir}")

    # Create Flask app with static and template folders
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=static_dir,
        static_url_path='/static',
        template_folder=template_dir
    )

    # Load configs
    app.config.from_object(Config)
    app.config.from_pyfile("config.py", silent=True)

    # CSRF protection
    csrf = CSRFProtect(app)
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())

    # Initialise extensions
    db.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    # Set up login
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(admin_bp)

    # Root and Dashboard routes
    
    # Landing page with link to dashboard
    @app.route("/")
    def index():
        return "Welcome to the RAG LLM Tool! Visit " + url_for("dashboard")
    
    # Dashboard route for displaying user document, queries and folders, protected by login
    @app.route("/dashboard")
    @login_required
    def dashboard():
        from .models import UploadedDocument, QueryHistory, Folder
        docs = UploadedDocument.query.filter_by(user_id=current_user.id) \
                  .order_by(UploadedDocument.upload_date.desc()).all()
        qs = QueryHistory.query.filter_by(user_id=current_user.id) \
                  .order_by(QueryHistory.timestamp.asc()).all()
        folders = Folder.query.filter_by(user_id=current_user.id).all()
        return render_template("dashboard.html", documents=docs, queries=qs, folders=folders)

    # Update last activity timestamp
    @app.before_request
    def update_last_activity():
        if current_user.is_authenticated:
            current_user.last_activity = datetime.utcnow()
            try:
                db.session.commit()
            except Exception as e:
                logger.error("Error updating last_activity: %s", e)
                db.session.rollback()

    # External utilities
    setup_pandoc()
    initialize_nltk_resources()

    return app

# Create the app instance
if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5500)
    # In production, use a WSGI server + reverse proxy
