from flask import Flask

from config import Config
from app.extensions import db, migrate, login_manager
from app.routes.admin import admin_bp
 
def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import models
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ---------------------------------------------------------
    # Business Types
    # ---------------------------------------------------------

    from app.business_types import BUSINESS_TYPES

    @app.context_processor
    def inject_business_types():
        return {
            "business_types": BUSINESS_TYPES
        }

    # ---------------------------------------------------------
    # Register blueprints
    # ---------------------------------------------------------

    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.business import business_bp
    from app.routes.category import category_bp
    from app.routes.product import product_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(admin_bp)
   
    return app
 
