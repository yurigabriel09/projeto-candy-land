import random
from sqlalchemy.orm import Session
from app.models.user import User


def request_login_code(db: Session, tipo: str, valor: str):
    if tipo != "email":
        return None

    user = db.query(User).filter(User.email == valor).first()

    if not user or not user.ativo:
        return None

    codigo = str(random.randint(100000, 999999))

    print(f"Código de autenticação para {user.email}: {codigo}")

    return {
        "usuario": user,
        "codigo": codigo
    }