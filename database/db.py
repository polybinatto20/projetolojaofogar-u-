import sqlite3  # Biblioteca padrão do Python para trabalhar com SQLite

from flask import g  # Objeto do Flask para armazenar dados durante a requisição

# Nome do arquivo do banco de dados
DATABASE = "FogareuClothes.db"

def get_db():
    # Verifica se já existe uma conexão salva no contexto da requisição
    if "db" not in g:
        # Se não existir, cria uma nova conexão com o banco
        g.db = sqlite3.connect(DATABASE)

        # Permite acessar os dados como dicionário (ex: linha["nome"])
        g.db.row_factory = sqlite3.Row

    # Retorna a conexão (nova ou já existente)
    return g.db


def close_db(e=None):
    # Remove a conexão do g (se existir) e retorna ela
    db = g.pop("db", None)

    # Se a conexão existir, fecha ela
    if db is not None:
        db.close()


def testar_conexao():
    try:
        db = get_db()  # tenta obter a conexão
        cursor = db.cursor()

        # Executa uma query simples (SQLite sempre aceita isso)
        cursor.execute("SELECT 1")

        print("Conexão com o banco funcionando!")
        return True

    except Exception as e:
        print("Erro ao conectar no banco:", e)
        return False