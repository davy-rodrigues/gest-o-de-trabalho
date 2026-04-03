import mysql.connector
from mysql.connector import Error
import streamlit as st

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'C#OrientadaObjeto', 
    'database': 'gestao_pendencias'
}

def conectar():
    """Conecta ao banco de dados MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Erro ao conectar ao MySQL: {e}")
        st.info("Certifique-se de que o MySQL está rodando e o banco 'gestao_pendencias' existe")
        return None

def criar_tabela():
    """Cria as tabelas necessárias se não existirem"""
    conn = conectar()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    # Criar banco de dados se não existir
    cursor.execute("CREATE DATABASE IF NOT EXISTS gestao_pendencias")
    cursor.execute("USE gestao_pendencias")
    
    # Tabela de tarefas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarefas (
            id VARCHAR(50) PRIMARY KEY,
            nome TEXT NOT NULL,
            status VARCHAR(20) NOT NULL,
            descricao TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de histórico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tarefa_id VARCHAR(50),
            acao TEXT,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()