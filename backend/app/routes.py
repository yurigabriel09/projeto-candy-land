from app.controllers.user_controller import user_bp

def register_routes(app):
    app.register_blueprint(user_bp)