from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.services import auth_service

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    tipo = data.get('tipo')
    valor = data.get('valor')

    if tipo not in ['email', 'phone'] or not valor:
        return jsonify({"detail": "Informe um tipo e um valor válidos"}), 400

    db = SessionLocal()
    try:
        resultado = auth_service.request_login_code(db, tipo, valor)

        if not resultado:
            return jsonify({"detail": "Usuário não encontrado"}), 404

        return jsonify({
            "message": "Código de autenticação gerado",
            "codigo": resultado["codigo"]
        }), 200
    finally:
        db.close()