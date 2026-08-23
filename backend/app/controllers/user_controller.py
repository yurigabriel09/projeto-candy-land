from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.services import user_service

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user_endpoint(user_id):
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        updated_user = user_service.update_user(
            db, 
            user_id, 
            nome=data.get('nome'), 
            email=data.get('email')
        )
        if not updated_user:
            return jsonify({"detail": "Usuário não encontrado"}), 404
        return jsonify({
            "id": updated_user.id,
            "nome": updated_user.nome,
            "email": updated_user.email,
            "ativo": updated_user.ativo
        }), 200
    finally:
        db.close()

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user_endpoint(user_id):
    db = SessionLocal()
    try:
        success = user_service.delete_user(db, user_id)
        if not success:
            return jsonify({"detail": "Usuário não encontrado"}), 404
        return '', 204
    finally:
        db.close()