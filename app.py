import streamlit as st
import pandas as pd
from database_sqlite import criar_tabela, query_to_df, execute_query
from datetime import datetime
import io
import hashlib

# Configuração da página para estilo corporativo
st.set_page_config(layout="wide", page_title="Enterprise Task Manager")

# Inicialização do Banco
criar_tabela()

# Gerenciamento de Estado
if 'tarefas_minimizadas' not in st.session_state:
    st.session_state.tarefas_minimizadas = set()
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = "expandido"
if 'task_id' not in st.session_state:
    st.session_state.task_id = None

# Funções Auxiliares
def gerar_id_unico(nome, descricao):
    conteudo = f"{nome}_{descricao}_{datetime.now()}".encode('utf-8')
    return hashlib.md5(conteudo).hexdigest()[:12]

def toggle_minimizar(tarefa_id):
    if tarefa_id in st.session_state.tarefas_minimizadas:
        st.session_state.tarefas_minimizadas.remove(tarefa_id)
    else:
        st.session_state.tarefas_minimizadas.add(tarefa_id)
    st.rerun()

# --- CSS CORPORATIVO (ESTILO SAAS / CLEAN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    @font-face {
        font-family: 'Segoe MDL2 Assets';
        src: local('Segoe MDL2 Assets'),
             url('https://cdn.jsdelivr.net/gh/microsoft/fonts@master/segoe-mdl2-assets.ttf') format('truetype');
    }

    :root {
        --primary: #2563eb;
        --bg-main: #f8fafc;
        --text-dark: #1e293b;
        --text-light: #64748b;
        --border: #e2e8f0;
        --card-bg: #ffffff;
    }

    .stApp {
        background-color: var(--bg-main);
        font-family: 'Inter', sans-serif;
        color: var(--text-dark);
    }

    h1, h2, h3 {
        font-weight: 600 !important;
        color: var(--text-dark) !important;
        letter-spacing: -0.5px !important;
    }

    /* Estilo de Card Corporativo */
    .task-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 0px;
        transition: box-shadow 0.2s;
    }
    .task-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-color: var(--primary);
    }

    /* Botões de Ação Dinâmicos */
    .stButton button {
        background: transparent !important;
        border: 1px solid var(--border) !important;
        font-family: 'Segoe MDL2 Assets', sans-serif !important;
        color: var(--text-light) !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        font-size: 16px !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: #eff6ff !important;
    }

    /* Mapeamento de Ícones Profissionais */
    div[data-key^="edit-"] button span::before { content: '\\E70F' !important; }
    div[data-key^="check-"] button span::before { content: '\\E73E' !important; }
    div[data-key^="pin-"] button span::before { content: '\\E840' !important; }
    div[data-key^="del-"] button span::before { content: '\\E74D' !important; }

    .stButton button span { font-size: 0 !important; }
    .stButton button span::before { font-size: 16px !important; display: inline-block; }

    /* Inputs Limpos */
    .stTextInput input, .stTextArea textarea {
        border-radius: 6px !important;
        border: 1px solid var(--border) !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Business Management")
st.caption("Sistema de Gestão de Pendências Operacionais")

# --- AREA DE CADASTRO ---
with st.expander("➕ Registrar Nova Pendência", expanded=False):
    with st.form("nova_tarefa", clear_on_submit=True):
        nome = st.text_input("Título")
        descricao = st.text_area("Descrição Detalhada")
        if st.form_submit_button("Confirmar Registro"):
            if nome:
                tid = gerar_id_unico(nome, descricao)
                execute_query("INSERT INTO tarefas (id, nome, status, descricao) VALUES (?, ?, ?, ?)", 
                              (tid, nome, "Pendente", descricao))
                st.rerun()

# --- DASHBOARD DE MÉTRICAS ---
df = query_to_df("SELECT * FROM tarefas ORDER BY data_criacao DESC")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Pendentes", len(df[df['status'] == 'Pendente']))
m2.metric("Em Curso", len(df[df['status'] == 'Em andamento']))
m3.metric("Concluídas", len(df[df['status'] == 'Concluído']))
m4.metric("Total Geral", len(df))

# --- KANBAN VIEW ---
st.divider()
k1, k2, k3 = st.columns(3)
colunas = [("Pendente", k1, "🔵"), ("Em andamento", k2, "🟡"), ("Concluído", k3, "🟢")]

for status_nome, coluna_st, icon in colunas:
    with coluna_st:
        st.subheader(f"{icon} {status_nome}")
        tarefas_col = df[df['status'] == status_nome]
        
        for _, t in tarefas_col.iterrows():
            tid = t['id']
            minimizada = tid in st.session_state.tarefas_minimizadas
            
            with st.container():
                if not minimizada:
                    # Renderiza Card Corporativo
                    st.markdown(f"""
                        <div class="task-card">
                            <div style="font-size: 0.85rem; color: #2563eb; font-weight: 500; margin-bottom: 4px;">ID: {tid}</div>
                            <div style="font-weight: 600; font-size: 1rem; color: #1e293b;">{t['nome']}</div>
                            <div style="font-size: 0.875rem; color: #64748b; margin-top: 6px;">{t['descricao'][:120] if t['descricao'] else 'Sem detalhes informados.'}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info(f"📄 {t['nome']}")

                # BOTÕES DE AÇÃO INTEGRADOS (LOGICAMENTE ABAIXO DO CARD)
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("e", key=f"edit-{tid}", help="Editar"):
                        st.session_state.task_id = tid
                        st.rerun()
                with b2:
                    if st.button("c", key=f"check-{tid}", help="Concluir"):
                        execute_query("UPDATE tarefas SET status='Concluído' WHERE id=?", (tid,))
                        st.rerun()
                with b3:
                    if st.button("p", key=f"pin-{tid}", help="Minimizar"):
                        toggle_minimizar(tid)
                with b4:
                    if st.button("d", key=f"del-{tid}", help="Excluir"):
                        execute_query("DELETE FROM tarefas WHERE id=?", (tid,))
                        st.rerun()
            st.write("") # Espaçador

# --- MODAL DE EDIÇÃO ---
if st.session_state.task_id:
    with st.sidebar:
        st.header("Propriedades da Tarefa")
        tid_edit = st.session_state.task_id
        dados = query_to_df("SELECT * FROM tarefas WHERE id=?", (tid_edit,)).iloc[0]
        
        n_nome = st.text_input("Nome", dados['nome'])
        n_desc = st.text_area("Descrição", dados['descricao'])
        n_status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluído"], 
                               index=["Pendente", "Em andamento", "Concluído"].index(dados['status']))
        
        if st.button("Salvar Alterações", use_container_width=True):
            execute_query("UPDATE tarefas SET nome=?, descricao=?, status=? WHERE id=?", (n_nome, n_desc, n_status, tid_edit))
            st.session_state.task_id = None
            st.rerun()
        if st.button("Descartar", use_container_width=True):
            st.session_state.task_id = None
            st.rerun()