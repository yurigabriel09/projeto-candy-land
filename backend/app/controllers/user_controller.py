from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.services import user_service

user_bp = Blueprint('user_bp', __name__)


@user_bp.route('/users', methods=['POST'])
def create_user_endpoint():
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        novo_user = user_service.create_user(
            db,
            nome=data.get('nome'),
            email=data.get('email')
        )
        return jsonify({
            "id": novo_user.id,
            "nome": novo_user.nome,
            "email": novo_user.email,
            "ativo": novo_user.ativo
        }), 201
    finally:
        db.close()


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_endpoint(user_id):
    db = SessionLocal()
    try:
        user = user_service.get_user(db, user_id)
        if not user:
            return jsonify({"detail": "Usuário não encontrado"}), 404
        return jsonify({
            "id": user.id,
            "nome": user.nome,
            "email": user.email,
            "ativo": user.ativo
        }), 200
    finally:
        db.close()


@user_bp.route('/users', methods=['GET'])
def get_users_endpoint():
    db = SessionLocal()
    try:
        users = user_service.get_users(db)
        return jsonify([{
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "ativo": u.ativo
        } for u in users]), 200
    finally:
        db.close()


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
        return 'Usuário deletado com sucesso', 200
    finally:
        db.close()