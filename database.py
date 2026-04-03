# database.py
import sqlite3
import streamlit as st

def conectar():
    return sqlite3.connect('pendencias.db', check_same_thread=False)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            status TEXT NOT NULL,
            descricao TEXT
        )
    ''')
    
    # Tabela de histórico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarefa_id INTEGER,
            acao TEXT,
            data TEXT
        )
    ''')
    
    conn.commit()
    conn.close()