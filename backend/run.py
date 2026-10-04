from app.config.config import Config
from app.database.database import db
from app.models.delivery import EntregaPedido
from app.models.order import Pedido
from app.routes.auth_routes import auth_bp
from app.routes.category_routes import categoria_bp
from app.routes.order_routes import pedido_bp
from app.routes.product_routes import produto_bp
from app.routes.restaurant_routes import restaurante_bp
from app.routes.user_routes import user_bp
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(user_bp)
    app.register_blueprint(restaurante_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(categoria_bp)
    app.register_blueprint(pedido_bp)
    return app


app = create_app()

with app.app_context():
    db.create_all()
    for pedido in Pedido.query.all():
        if not EntregaPedido.query.filter_by(pedido_id=pedido.id).first():
            status = (
                "CANCELADO"
                if pedido.status == "CANCELADO"
                else "ENTREGA_CONCLUIDA"
                if pedido.delivered_at
                else "NAO_SOLICITADO"
            )
            db.session.add(
                EntregaPedido(
                    pedido_id=pedido.id,
                    status=status,
                    concluida_em=pedido.delivered_at,
                )
            )
    db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
