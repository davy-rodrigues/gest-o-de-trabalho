from sqlalchemy import create_engine, text
import streamlit as st

# Configurações do banco
DB_USER = "root"
DB_PASSWORD = "C#OrientadaObjeto"
DB_HOST = "127.0.0.1"  # Altere para o IP da outra máquina
DB_NAME = "gestao_pendencias"
DB_PORT = 3306

def get_engine():
    """Retorna a conexão com o MySQL"""
    try:
        conexao_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(conexao_str, pool_pre_ping=True, pool_recycle=3600)
        
        # Testa conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        st.sidebar.success(f"✅ Conectado ao MySQL em {DB_HOST}")
        return engine
        
    except Exception as e:
        st.sidebar.error(f"❌ Erro ao conectar: {e}")
        return None

def criar_tabela():
    """Cria as tabelas no banco de dados"""
    engine = get_engine()
    if engine is None:
        return

    try:
        with engine.begin() as conn:
            # Tabela tarefas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tarefas (
                    id VARCHAR(50) PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    descricao TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))
            
            # Tabela historico
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historico (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tarefa_id VARCHAR(50),
                    acao TEXT,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
        st.sidebar.success("✅ Tabelas prontas!")
        
    except Exception as e:
        st.error(f"❌ Erro: {e}")