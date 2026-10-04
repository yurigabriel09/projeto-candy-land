# PROJETO CANDYLAND

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


## 📦 Regras de negócio e modelo de dados

A documentação funcional do projeto fica centralizada em `docs/`.

- `docs/requisitos.md` — regras de negócio gerais.
- `docs/regras-pedidos.md` — ciclo do pedido, ciclo da entrega, transições e exceções.
- `docs/modelo-dados.md` — visão do modelo físico atual em diagrama ER.

### Regra de manutenção da documentação

Toda alteração que mudar uma regra de negócio deve atualizar a documentação correspondente e seus testes automatizados. Toda alteração estrutural no banco também deve atualizar `docs/modelo-dados.md`.

### Testes de regras de negócio

Os testes automatizados ficam em `backend/tests/`. Para executar a suíte: 

```bash
cd backend
pip install -r requirements.txt
pytest -q
```
