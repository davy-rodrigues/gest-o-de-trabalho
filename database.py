from sqlalchemy import create_engine, text
import streamlit as st

# Configurações do banco - ALTERE PARA O IP DA SUA OUTRA MÁQUINA
DB_USER = "root"
DB_PASSWORD = "C#OrientadaObjeto"
DB_HOST = "127.0.0.1"  # ← Coloque o IP da sua outra máquina (ex: 192.168.1.100)
DB_NAME = "gestao_pendencias"
DB_PORT = 3306

def get_engine():
    """Retorna a conexão com o MySQL na outra máquina"""
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
        st.sidebar.info("""
        **Verifique:**
        1. O MySQL está rodando na outra máquina?
        2. O IP está correto?
        3. A porta 3306 está liberada?
        4. Execute na outra máquina:
           ```sql
           CREATE USER 'root'@'%' IDENTIFIED BY 'C#OrientadaObjeto';
           GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';
           FLUSH PRIVILEGES;
""")