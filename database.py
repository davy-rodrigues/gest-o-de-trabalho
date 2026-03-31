import sqlite3

def conectar():
    return sqlite3.connect("tarefas.db", check_same_thread=False)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    # Tabela principal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tarefas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        status TEXT,
        descricao TEXT
    )
    """)

    # Tabela de histórico
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarefa_id INTEGER,
        acao TEXT,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()