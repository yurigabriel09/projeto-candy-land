# projeto-candy-land

Este projeto é uma aplicação full-stack composta por uma API Backend em Python (FastAPI/SQLAlchemy) e um Frontend em React.

## 🛠️ Tecnologias Utilizadas
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, SQLite/PostgreSQL
- **Frontend**: React, Node.js, Vite/Create React App

---

## 🚀 Instruções de Instalação

### Prerequisites
- Python 3.10 ou superior
- Node.js v18 ou superior e npm

### 1. Configurando o Backend
```bash
# Entre na pasta do backend
cd backend

# Crie um ambiente virtual (opcional, mas recomendado)
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Em um novo terminal, entre na pasta do frontend
cd frontend

# Instale as dependências do Node
npm install

# Dentro do diretório /backend com o venv ativado
python run.py

# Dentro do diretório /frontend
npm start
# ou se estiver usando Vite:
npm run dev