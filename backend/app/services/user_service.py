from sqlalchemy.orm import Session
from app.models.user import User


def create_user(db: Session, nome: str, email: str):
    novo_user = User(nome=nome, email=email)
    db.add(novo_user)
    db.commit()
    db.refresh(novo_user)
    return novo_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session):
    return db.query(User).all()

def update_user(db: Session, user_id: int, nome: str = None, email: str = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    if nome is not None:
        user.nome = nome
    if email is not None:
        user.email = email
        
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True