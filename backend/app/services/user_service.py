from sqlalchemy.orm import Session
from app.models.user import User

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