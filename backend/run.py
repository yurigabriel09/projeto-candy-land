from flask import Flask
from flask_cors import CORS
from app.database import engine, Base
from app.controllers.user_controller import user_bp

# Criar tabelas no banco SQLite automaticamente
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)
app.register_blueprint(user_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)