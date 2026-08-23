from app.database import engine, Base
# Importar os modelos garante que a Base conheça as tabelas antes de criá-las
from app.models import User 

def init_db():
    print("Conectando ao banco SQLite e criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas 'bases' e estrutura do banco criadas com sucesso!")

if __name__ == "__main__":
    init_db()