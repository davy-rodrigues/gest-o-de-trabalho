import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import os

DB_PATH = "gestao_pendencias.db"

def get_connection():
    """Retorna conexão com SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    """Cria as tabelas necessárias se não existirem"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Cria tabela tarefas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas (
                id VARCHAR(12) PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                status TEXT DEFAULT 'Pendente',
                descricao TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cria tabela historico
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarefa_id VARCHAR(12),
                acao TEXT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao criar tabelas: {e}")
        return False

def get_engine():
    """Retorna None para compatibilidade (não usado com SQLite)"""
    return None

def query_to_df(query, params=None):
    """Executa query SELECT e retorna DataFrame"""
    conn = get_connection()
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def execute_query(query, params=None):
    """Executa query de escrita (INSERT, UPDATE, DELETE)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    conn.commit()
    conn.close()

def execute_many(query, params_list):
    """Executa múltiplas queries"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(query, params_list)
    conn.commit()
    conn.close()