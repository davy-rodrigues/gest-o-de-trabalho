from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import streamlit as st
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurações do banco
DB_USER = "root"
DB_HOST = "127.0.0.1"
DB_NAME = "gestao_pendencias"
DB_PORT = 3306

def get_password():
    """Retorna a senha do banco"""
    password = os.getenv('DB_PASSWORD')
    if password:
        return password
    else:
        st.error("❌ Senha do banco não encontrada no .env")
        return None

def criar_banco_se_nao_existe():
    """Cria o banco de dados se ele não existir"""
    try:
        password = get_password()
        if not password:
            return False
            
        # Conecta sem especificar o banco - sem auth_plugin
        conn_str = f"mysql+pymysql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}"
        engine_sem_db = create_engine(conn_str)
        
        with engine_sem_db.connect() as conn:
            # Verifica se o banco existe
            result = conn.execute(text(f"SHOW DATABASES LIKE '{DB_NAME}'"))
            existe = result.fetchone()
            
            if not existe:
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                conn.commit()
                st.sidebar.success(f"✅ Banco de dados '{DB_NAME}' criado com sucesso!")
            else:
                st.sidebar.info(f"📦 Banco de dados '{DB_NAME}' já existe")
                
        engine_sem_db.dispose()
        return True
        
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao verificar/criar banco: {e}")
        return False

def get_engine():
    """Retorna a conexão com o MySQL"""
    try:
        # Primeiro, garante que o banco existe
        if not criar_banco_se_nao_existe():
            return None
            
        password = get_password()
        if not password:
            return None
            
        # Conecta ao banco específico - sem auth_plugin
        conexao_str = f"mysql+pymysql://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        engine = create_engine(
            conexao_str, 
            pool_pre_ping=True, 
            pool_recycle=3600
        )
        
        # Testa conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        st.sidebar.success("✅ Conectado ao MySQL com sucesso!")
        return engine
        
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao conectar: {e}")
        return None

def criar_tabela():
    """Cria as tabelas necessárias se não existirem"""
    engine = get_engine()
    if engine is None:
        return False
    
    try:
        with engine.connect() as conn:
            # Cria tabela tarefas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tarefas (
                    id VARCHAR(12) PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    status ENUM('Pendente', 'Em andamento', 'Concluído') DEFAULT 'Pendente',
                    descricao TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Cria tabela historico
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historico (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tarefa_id VARCHAR(12),
                    acao TEXT,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE
                )
            """))
            
            conn.commit()
            st.sidebar.success("✅ Tabelas criadas/verificadas com sucesso!")
            return True
            
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao criar tabelas: {e}")
        return False
    finally:
        engine.dispose()