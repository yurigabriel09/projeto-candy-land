from flask import Flask
from flask_cors import CORS
from app.config.config import Config
from app.database.database import db
from app.routes.user_routes import user_bp
from app.routes.restaurant_routes import restaurante_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(user_bp)
    app.register_blueprint(restaurante_bp)

    return app

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)