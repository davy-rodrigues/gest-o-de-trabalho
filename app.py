import streamlit as st
import pandas as pd
from database_sqlite import criar_tabela, query_to_df, execute_query, get_connection
from datetime import datetime
import io
import hashlib

st.set_page_config(layout="wide", page_title="Gestão de Pendências", page_icon="📋")

# Conecta ao banco SQLite
criar_tabela()

# Inicializa session state
if 'tarefas_minimizadas' not in st.session_state:
    st.session_state.tarefas_minimizadas = set()
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = "expandido"
if 'task_id' not in st.session_state:
    st.session_state.task_id = None
if 'filtro_status' not in st.session_state:
    st.session_state.filtro_status = "Todos"

def gerar_id_unico(nome, descricao):
    conteudo = f"{nome}_{descricao}_{datetime.now().timestamp()}".encode('utf-8')
    return hashlib.md5(conteudo).hexdigest()[:12]

def toggle_minimizar(tarefa_id):
    if tarefa_id in st.session_state.tarefas_minimizadas:
        st.session_state.tarefas_minimizadas.remove(tarefa_id)
    else:
        st.session_state.tarefas_minimizadas.add(tarefa_id)
    st.rerun()

def toggle_todas_minimizar():
    if st.session_state.modo_visualizacao == "expandido":
        st.session_state.modo_visualizacao = "minimizado"
        df_atual = query_to_df("SELECT id FROM tarefas")
        for id_tarefa in df_atual['id'].values:
            st.session_state.tarefas_minimizadas.add(id_tarefa)
    else:
        st.session_state.modo_visualizacao = "expandido"
        st.session_state.tarefas_minimizadas.clear()
    st.rerun()

# CSS Modernizado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&display=swap');

    :root {
        --bg-dark: #020205;
        --bg-card: rgba(13, 17, 23, 0.8);
        --neon-cyan: #00f2ff;
        --neon-blue: #0066ff;
        --neon-purple: #bc6ff1;
        --text-main: #e0faff;
        --text-dim: #88a0b0;
        --transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .stApp {
        background-color: var(--bg-dark);
        background-image: 
            radial-gradient(at 0% 0%, rgba(188, 111, 241, 0.15) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(0, 242, 255, 0.1) 0px, transparent 50%),
            linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 50px 50px, 50px 50px;
        color: var(--text-main);
    }

    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 2px !important;
        background: linear-gradient(135deg, var(--neon-cyan) 30%, var(--neon-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 12px rgba(0, 242, 255, 0.4));
        text-transform: uppercase;
    }

    /* Cards modernos */
    .task-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        transition: var(--transition);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
    }

    .task-card:hover {
        transform: translateY(-5px);
        border-color: var(--neon-purple);
        box-shadow: 0 0 30px rgba(188, 111, 241, 0.2);
    }

    .task-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 10px;
        color: var(--neon-cyan);
    }

    .task-description {
        font-size: 14px;
        color: var(--text-dim);
        margin-bottom: 15px;
    }

    /* Botões estilizados */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 242, 255, 0.1), rgba(188, 111, 241, 0.1));
        border: 1px solid rgba(0, 242, 255, 0.3);
        color: var(--text-main);
        backdrop-filter: blur(5px);
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 500;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        border-color: var(--neon-purple);
        box-shadow: 0 0 20px rgba(188, 111, 241, 0.3);
        background: linear-gradient(135deg, rgba(0, 242, 255, 0.2), rgba(188, 111, 241, 0.2));
    }

    /* Inputs estilizados */
    .stTextInput input, .stTextArea textarea {
        background: rgba(0, 0, 0, 0.6) !important;
        border: 1px solid rgba(0, 242, 255, 0.3) !important;
        border-radius: 8px !important;
        color: var(--text-main) !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--neon-purple) !important;
        box-shadow: 0 0 10px rgba(188, 111, 241, 0.3) !important;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-pendente { background: rgba(255, 59, 48, 0.2); color: #ff3b30; border: 1px solid #ff3b30; }
    .status-andamento { background: rgba(255, 204, 0, 0.2); color: #ffcc00; border: 1px solid #ffcc00; }
    .status-concluido { background: rgba(52, 199, 89, 0.2); color: #34c759; border: 1px solid #34c759; }

    /* Métricas */
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(0, 242, 255, 0.2);
    }

    /* Esconder elementos padrão */
    #MainMenu, footer, header {visibility: hidden;}
    
    hr {
        border-color: rgba(188, 111, 241, 0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("📋 Gestão Inteligente de Pendências")

# Botão minimizar/expandir todas
col_botoes_top, col_filtro = st.columns([1, 3])
with col_botoes_top:
    if st.session_state.modo_visualizacao == "expandido":
        if st.button("📌 Minimizar Todas", use_container_width=True):
            toggle_todas_minimizar()
    else:
        if st.button("📂 Expandir Todas", use_container_width=True):
            toggle_todas_minimizar()

with col_filtro:
    filtro = st.selectbox("Filtrar por status", ["Todos", "Pendente", "Em andamento", "Concluído"], 
                          key="filtro_status_select")
    if filtro != st.session_state.filtro_status:
        st.session_state.filtro_status = filtro
        st.rerun()

# NOVA TAREFA
with st.expander("✨ Criar Nova Pendência", expanded=False):
    with st.form("nova_tarefa"):
        nome = st.text_input("Nome da pendência", placeholder="Digite o título da tarefa...")
        descricao = st.text_area("Descrição", placeholder="Descreva os detalhes da tarefa...")

        if st.form_submit_button("➕ Adicionar", use_container_width=True):
            if nome and nome.strip():
                tarefa_id = gerar_id_unico(nome.strip(), descricao.strip())
                
                # Verifica se já existe
                df_existente = query_to_df("SELECT id FROM tarefas WHERE nome = ?", (nome.strip(),))
                
                if not df_existente.empty:
                    st.warning("⚠️ Já existe uma tarefa com este nome!")
                else:
                    execute_query(
                        "INSERT INTO tarefas (id, nome, status, descricao) VALUES (?, ?, ?, ?)",
                        (tarefa_id, nome.strip(), "Pendente", descricao.strip() or "Sem descrição")
                    )
                    execute_query(
                        "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                        (tarefa_id, "Tarefa criada")
                    )
                    st.success("✅ Pendência criada com sucesso!")
                    st.rerun()
            else:
                st.warning("⚠️ Nome não pode ser vazio")

# IMPORTAR EXCEL
with st.expander("📎 Importar Excel", expanded=False):
    arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

    if arquivo:
        df_import = pd.read_excel(arquivo)
        st.write("**Colunas encontradas:**", list(df_import.columns))
        
        df_import.columns = df_import.columns.str.strip().str.lower()
        st.dataframe(df_import.head())

        if st.button("🚀 Importar pendências"):
            inseridos = 0
            ignorados = 0

            for _, row in df_import.iterrows():
                # Identifica colunas
                nome = descricao = ""
                for col in df_import.columns:
                    if any(p in col for p in ['nome', 'titulo', 'tarefa']):
                        nome = str(row.get(col, "")).strip()
                    if any(p in col for p in ['descricao', 'desc']):
                        descricao = str(row.get(col, "")).strip()
                
                if not nome or nome == "nan":
                    continue
                
                # Gera ID
                tarefa_id = gerar_id_unico(nome, descricao)
                
                # Verifica se já existe
                df_existente = query_to_df("SELECT id FROM tarefas WHERE nome = ?", (nome,))
                if not df_existente.empty:
                    ignorados += 1
                    continue
                
                # Insere
                execute_query(
                    "INSERT INTO tarefas (id, nome, status, descricao) VALUES (?, ?, ?, ?)",
                    (tarefa_id, nome, "Pendente", descricao or "Sem descrição")
                )
                execute_query(
                    "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                    (tarefa_id, "Importado via Excel")
                )
                inseridos += 1
            
            st.success(f"✅ Importação concluída! Inseridos: {inseridos}, Ignorados (duplicados): {ignorados}")
            st.rerun()

# DASHBOARD
st.divider()
st.subheader("📊 Dashboard")

# Filtra dados para o dashboard
df_completo = query_to_df("SELECT * FROM tarefas ORDER BY data_criacao DESC")

# Aplica filtro
if st.session_state.filtro_status != "Todos":
    df = df_completo[df_completo['status'] == st.session_state.filtro_status]
else:
    df = df_completo

# Métricas
col1, col2, col3, col4 = st.columns(4)
with col1:
    pendentes = len(df_completo[df_completo['status'] == 'Pendente'])
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2em;">🔴</div>
        <div style="font-size: 1.5em; font-weight: bold;">{pendentes}</div>
        <div>Pendentes</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    andamento = len(df_completo[df_completo['status'] == 'Em andamento'])
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2em;">🟡</div>
        <div style="font-size: 1.5em; font-weight: bold;">{andamento}</div>
        <div>Em andamento</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    concluidos = len(df_completo[df_completo['status'] == 'Concluído'])
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2em;">🟢</div>
        <div style="font-size: 1.5em; font-weight: bold;">{concluidos}</div>
        <div>Concluídos</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 2em;">📊</div>
        <div style="font-size: 1.5em; font-weight: bold;">{len(df_completo)}</div>
        <div>Total</div>
    </div>
    """, unsafe_allow_html=True)

# KANBAN
st.divider()
st.subheader("📌 Quadro Kanban")

if st.session_state.filtro_status == "Todos":
    col1, col2, col3 = st.columns(3)
    
    def render_coluna(status, coluna, emoji):
        with coluna:
            st.markdown(f"### {emoji} {status}")
            tarefas = df_completo[df_completo["status"] == status]
            
            if len(tarefas) == 0:
                st.info(f"Nenhuma tarefa {status.lower()}")
            
            for _, t in tarefas.iterrows():
                tarefa_id = t['id']
                esta_minimizada = tarefa_id in st.session_state.tarefas_minimizadas
                
                if esta_minimizada:
                    col_a, col_b, col_c, col_d = st.columns([4, 1, 1, 1])
                    with col_a:
                        if st.button(f"📄 {t['nome'][:40]}", key=f"min_{tarefa_id}"):
                            toggle_minimizar(tarefa_id)
                    with col_b:
                        if st.button("✏️", key=f"edit_icon_{tarefa_id}"):
                            st.session_state.task_id = tarefa_id
                    with col_c:
                        if status != "Concluído":
                            if st.button("✅", key=f"comp_icon_{tarefa_id}"):
                                execute_query("UPDATE tarefas SET status='Concluído' WHERE id=?", (tarefa_id,))
                                execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, "Tarefa concluída"))
                                st.rerun()
                    with col_d:
                        if st.button("🗑️", key=f"del_icon_{tarefa_id}"):
                            execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, f"Excluída"))
                            execute_query("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
                            st.rerun()
                else:
                    st.markdown(f"""
                    <div class="task-card">
                        <div class="task-title">📌 {t['nome']}</div>
                        <div class="task-description">{t['descricao'][:100] if t['descricao'] else 'Sem descrição'}</div>
                        <div class="status-badge status-{status.lower().replace(' ', '-')}">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    b1, b2, b3, b4 = st.columns(4)
                    with b1:
                        if st.button("✏️ Editar", key=f"edit_{status}_{tarefa_id}"):
                            st.session_state.task_id = tarefa_id
                    with b2:
                        if status != "Concluído":
                            if st.button("✅ Concluir", key=f"comp_{tarefa_id}"):
                                execute_query("UPDATE tarefas SET status='Concluído' WHERE id=?", (tarefa_id,))
                                execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, "Tarefa concluída"))
                                st.rerun()
                    with b3:
                        if st.button("📌 Minimizar", key=f"min_{status}_{tarefa_id}"):
                            toggle_minimizar(tarefa_id)
                    with b4:
                        if st.button("🗑️ Excluir", key=f"del_{status}_{tarefa_id}"):
                            execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, "Excluída"))
                            execute_query("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
                            st.rerun()
                
                st.markdown("---")
    
    render_coluna("Pendente", col1, "🔴")
    render_coluna("Em andamento", col2, "🟡")
    render_coluna("Concluído", col3, "🟢")
else:
    # Visualização em lista quando filtrado
    st.markdown(f"### Mostrando tarefas com status: **{st.session_state.filtro_status}**")
    for _, t in df.iterrows():
        tarefa_id = t['id']
        with st.container():
            st.markdown(f"""
            <div class="task-card">
                <div class="task-title">📌 {t['nome']}</div>
                <div class="task-description">{t['descricao'][:200] if t['descricao'] else 'Sem descrição'}</div>
                <div class="status-badge status-{t['status'].lower().replace(' ', '-')}">{t['status']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("✏️ Editar", key=f"edit_filtro_{tarefa_id}"):
                    st.session_state.task_id = tarefa_id
            with col2:
                if t['status'] != "Concluído":
                    if st.button("✅ Concluir", key=f"comp_filtro_{tarefa_id}"):
                        execute_query("UPDATE tarefas SET status='Concluído' WHERE id=?", (tarefa_id,))
                        execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, "Tarefa concluída"))
                        st.rerun()
            with col3:
                if st.button("📌 Detalhes", key=f"detail_filtro_{tarefa_id}"):
                    st.session_state.task_id = tarefa_id
            with col4:
                if st.button("🗑️ Excluir", key=f"del_filtro_{tarefa_id}"):
                    execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", (tarefa_id, "Excluída"))
                    execute_query("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
                    st.rerun()
            st.markdown("---")

# EDITAR TAREFA
if st.session_state.task_id:
    tarefa_id = st.session_state.task_id
    df_tarefa = query_to_df("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,))
    
    if not df_tarefa.empty:
        tarefa = df_tarefa.iloc[0]
        st.divider()
        st.subheader(f"✏️ Editando: {tarefa['nome']}")
        
        with st.form(key=f"edit_form_{tarefa_id}"):
            novo_nome = st.text_input("Nome", tarefa['nome'])
            nova_desc = st.text_area("Descrição", tarefa['descricao'] if tarefa['descricao'] else "")
            novo_status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluído"], 
                                      index=["Pendente", "Em andamento", "Concluído"].index(tarefa['status']))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("💾 Salvar"):
                    execute_query("UPDATE tarefas SET nome=?, descricao=?, status=? WHERE id=?", 
                                 (novo_nome, nova_desc, novo_status, tarefa_id))
                    execute_query("INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)", 
                                 (tarefa_id, f"Tarefa editada - Status: {novo_status}"))
                    st.session_state.task_id = None
                    st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state.task_id = None
                    st.rerun()
    else:
        st.warning("⚠️ Tarefa não encontrada!")
        st.session_state.task_id = None
        st.rerun()

# EXPORTAR DADOS
st.divider()
st.subheader("📥 Exportar Dados")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 Exportar Tarefas", use_container_width=True):
        df_export = query_to_df("SELECT * FROM tarefas ORDER BY status, data_criacao")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Tarefas", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar Excel", data=output, 
                          file_name=f"tarefas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True)

with col2:
    if st.button("📜 Exportar Histórico", use_container_width=True):
        df_hist = query_to_df("SELECT * FROM historico ORDER BY data DESC")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_hist.to_excel(writer, sheet_name="Historico", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar Excel", data=output,
                          file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True)

# Rodapé
st.markdown("""
<div class="custom-footer" style="text-align: center; padding: 20px; margin-top: 50px;">
    <p style="color: #88a0b0;">🚀 Gestão Inteligente de Pendências | Sistema desenvolvido com Streamlit</p>
</div>
""", unsafe_allow_html=True)