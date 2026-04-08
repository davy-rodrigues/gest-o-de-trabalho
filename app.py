import streamlit as st
import pandas as pd
from database_sqlite import criar_tabela, query_to_df, execute_query, get_connection
from datetime import datetime
import io
import hashlib




st.set_page_config(layout="wide")

# Conecta ao banco SQLite
criar_tabela()


if 'tarefas_minimizadas' not in st.session_state:
    st.session_state.tarefas_minimizadas = set()
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = "expandido"
if 'task_id' not in st.session_state:
    st.session_state.task_id = None


def gerar_id_unico(nome, descricao):
    conteudo = f"{nome}_{descricao}".encode('utf-8')
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

    /* Fundo com efeito de malha tecnológica */
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

    /* Títulos Magníficos */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 2px !important;
        background: linear-gradient(135deg, var(--neon-cyan) 30%, var(--neon-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 12px rgba(0, 242, 255, 0.4));
        text-transform: uppercase;
    }

    /* Cards com Borda Animada Sutil */
    .card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 24px;
        position: relative;
        overflow: hidden;
        transition: var(--transition);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
    }

    .card::before {
        content: "";
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(188, 111, 241, 0.1), transparent);
        transition: 0.8s;
    }

    .card:hover::before {
        left: 100%;
    }

    .card:hover {
        transform: scale(1.02) translateY(-5px);
        border-color: var(--neon-purple);
        box-shadow: 0 0 30px rgba(188, 111, 241, 0.2);
    }

    /* Botões Ghost - Agora com mais presença */
    .stButton button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 242, 255, 0.3) !important; /* Aumentada a visibilidade inicial */
        color: var(--text-main) !important;
        opacity: 0.8; /* Mais visível por padrão */
        backdrop-filter: blur(5px);
        font-family: 'Inter', sans-serif !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
    }

    .stButton button:hover {
        opacity: 1 !important;
        background: linear-gradient(135deg, rgba(0, 242, 255, 0.2), rgba(188, 111, 241, 0.2)) !important;
        border-color: var(--neon-purple) !important;
        box-shadow: 0 0 20px rgba(188, 111, 241, 0.5) !important;
        color: white !important;
    }

    /* Inputs estilo "Cyberpunk Terminal" */
    .stTextInput input {
        background: rgba(0, 0, 0, 0.6) !important;
        border-left: 4px solid var(--neon-cyan) !important;
        border-right: 1px solid rgba(0, 242, 255, 0.2) !important;
        border-top: 1px solid rgba(0, 242, 255, 0.2) !important;
        border-bottom: 1px solid rgba(0, 242, 255, 0.2) !important;
        border-radius: 4px !important;
        font-family: 'Consolas', monospace;
    }

    /* Status Badge com Brilho Pulsante */
    .status-badge {
        position: relative;
        padding: 5px 15px;
        background: rgba(0, 242, 255, 0.05);
        border: 1px solid var(--neon-cyan);
        color: var(--neon-cyan);
        border-radius: 50px;
        font-size: 11px;
        text-transform: uppercase;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(0, 242, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0); }
    }

    /* Rodapé Sci-Fi */
    .custom-footer {
        background: linear-gradient(transparent, rgba(188, 111, 241, 0.05));
        border-top: 1px solid rgba(188, 111, 241, 0.2);
        padding: 40px;
        text-align: center;
        margin-top: 100px;
    }

    /* Esconder elementos padrão do Streamlit para um visual limpo */
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("📋 Gestão Inteligente de Pendências")

# Botão minimizar/expandir todas
col_botoes_top, _ = st.columns([1, 3])
with col_botoes_top:
    if st.session_state.modo_visualizacao == "expandido":
        if st.button("📌 Minimizar Todas", use_container_width=True, help="Minimizar todas as tarefas para economia de espaço"):
            toggle_todas_minimizar()
    else:
        if st.button("📂 Expandir Todas", use_container_width=True, help="Expandir todas as tarefas para visualização completa"):
            toggle_todas_minimizar()


# NOVA TAREFA

with st.form("nova_tarefa"):
    st.markdown("### ✨ Criar Nova Pendência")
    nome = st.text_input("Nome da pendência", placeholder="Digite o título da tarefa...")
    descricao = st.text_area("Descrição", placeholder="Descreva os detalhes da tarefa...")

    if st.form_submit_button("➕ Adicionar", help="Clique para criar uma nova tarefa"):
        if nome.strip():
            tarefa_id = gerar_id_unico(nome.strip(), descricao.strip())
            
            # Verifica se já existe
            df_existente = query_to_df("SELECT id FROM tarefas WHERE id = ?", (tarefa_id,))
            
            if not df_existente.empty:
                st.warning("⚠️ Esta tarefa já existe!")
            else:
                execute_query(
                    "INSERT INTO tarefas (id, nome, status, descricao) VALUES (?, ?, ?, ?)",
                    (tarefa_id, nome.strip(), "Pendente", descricao.strip())
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

st.divider()
st.subheader("📎 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"], help="Arquivos suportados: .xlsx")

if arquivo:
    df_import = pd.read_excel(arquivo)
    st.write("**Colunas encontradas:**", list(df_import.columns))
    
    # Normaliza colunas
    df_import.columns = df_import.columns.str.strip().str.lower()
    st.dataframe(df_import)

    if st.button("🚀 Importar pendências", help="Importar tarefas do Excel para o sistema"):
        inseridos_pendente = inseridos_andamento = inseridos_concluido = 0
        ignorados_excluidos = ignorados_duplicados = 0

        for _, row in df_import.iterrows():
            # Identifica colunas
            nome = descricao = status_raw = ""
            for col in df_import.columns:
                if any(p in col for p in ['nome', 'titulo', 'tarefa']):
                    nome = str(row.get(col, "")).strip()
                if any(p in col for p in ['descricao', 'desc']):
                    descricao = str(row.get(col, "")).strip()
                if any(p in col for p in ['status', 'situacao']):
                    status_raw = str(row.get(col, "")).strip().lower()
            
            if not nome or nome == "nan":
                continue
            
            # Processa status
            status = "Pendente"
            if "pendente" in status_raw or "aberto" in status_raw:
                status = "Pendente"
                inseridos_pendente += 1
            elif "andamento" in status_raw or "progresso" in status_raw:
                status = "Em andamento"
                inseridos_andamento += 1
            elif "conclu" in status_raw or "finalizado" in status_raw:
                status = "Concluído"
                inseridos_concluido += 1
            elif "exclu" in status_raw:
                ignorados_excluidos += 1
                continue
            else:
                inseridos_pendente += 1
            
            # Gera ID
            tarefa_id = gerar_id_unico(nome, descricao)
            
            # Verifica se já existe
            df_existente = query_to_df("SELECT id FROM tarefas WHERE id = ?", (tarefa_id,))
            if not df_existente.empty:
                ignorados_duplicados += 1
                continue
            
            # Insere
            execute_query(
                "INSERT INTO tarefas (id, nome, status, descricao) VALUES (?, ?, ?, ?)",
                (tarefa_id, nome, status, descricao or "Sem descrição")
            )
            execute_query(
                "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                (tarefa_id, f"Importado via Excel (Status: {status})")
            )
        
        st.success(f"""
        ✅ Importação concluída!
        - 📝 Pendentes: {inseridos_pendente}
        - ⚙️ Em andamento: {inseridos_andamento}
        - ✅ Concluídos: {inseridos_concluido}
        - ⏭ Duplicados ignorados: {ignorados_duplicados}
        - 🗑️ Excluídos ignorados: {ignorados_excluidos}
        """)
        st.rerun()


# DASHBOARD

df = query_to_df("SELECT * FROM tarefas ORDER BY data_criacao DESC")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🔴 Pendentes", len(df[df['status'] == 'Pendente']))
with col2:
    st.metric("🟡 Em andamento", len(df[df['status'] == 'Em andamento']))
with col3:
    st.metric("🟢 Concluídos", len(df[df['status'] == 'Concluído']))
with col4:
    st.metric("📊 Total", len(df))

# KANBAN

st.divider()
st.subheader("📌 Status Atividades")

col1, col2, col3 = st.columns(3)

def render_coluna(status, coluna, cor):
    with coluna:
        st.markdown(f"### {cor} {status}")
        tarefas = df[df["status"] == status]
        
        if len(tarefas) == 0:
            st.info(f"Nenhuma tarefa {status.lower()}")
        
        for _, t in tarefas.iterrows():
            tarefa_id = t['id']
            esta_minimizada = tarefa_id in st.session_state.tarefas_minimizadas
            
            if st.session_state.modo_visualizacao == "minimizado" and not esta_minimizada:
                esta_minimizada = True
                st.session_state.tarefas_minimizadas.add(tarefa_id)
            
            if esta_minimizada:
                col_a, col_b, col_c = st.columns([4, 1, 1])
                with col_a:
                    if st.button(f"📄 {t['nome'][:40]}", key=f"min_{tarefa_id}", help="Clique para expandir"):
                        toggle_minimizar(tarefa_id)
                with col_b:
                    if st.button("✏️", key=f"edit_{tarefa_id}", help="Editar tarefa"):
                        st.session_state.task_id = tarefa_id
                with col_c:
                    if st.button("🗑️", key=f"del_{tarefa_id}", help="Excluir tarefa"):
                        execute_query(
                            "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                            (tarefa_id, f"Excluída - Status: {t['status']}")
                        )
                        execute_query("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
                        st.rerun()
            else:
                st.markdown(f"""
                <div class="card">
                    <div class="titulo">📌 {t['nome']}</div>
                    <div class="desc">{t['descricao'][:100] if t['descricao'] else 'Sem descrição'}...</div>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("✏️", key=f"edit_{status}_{tarefa_id}", help="Editar tarefa"):
                        st.session_state.task_id = tarefa_id
                with b2:
                    if status != "Concluído":
                        if st.button("✅", key=f"comp_{tarefa_id}", help="Marcar como concluída"):
                            execute_query(
                                "UPDATE tarefas SET status='Concluído' WHERE id=?",
                                (tarefa_id,)
                            )
                            execute_query(
                                "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                                (tarefa_id, "Tarefa concluída")
                            )
                            st.rerun()
                with b3:
                    if st.button("📌", key=f"min_{status}_{tarefa_id}", help="Minimizar/Expandir"):
                        toggle_minimizar(tarefa_id)
                with b4:
                    if st.button("🗑️", key=f"del_{status}_{tarefa_id}", help="Excluir tarefa"):
                        execute_query(
                            "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                            (tarefa_id, f"Excluída - Status: {t['status']}")
                        )
                        execute_query("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
                        st.rerun()
            
            st.markdown("---")

render_coluna("Pendente", col1, "🔴")
render_coluna("Em andamento", col2, "🟡")
render_coluna("Concluído", col3, "🟢")

# DETALHE DA TAREFA

if st.session_state.task_id:
    tarefa_id = st.session_state.task_id
    
    df_tarefa = query_to_df("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,))
    
    if not df_tarefa.empty:
        tarefa = df_tarefa.iloc[0]
        st.divider()
        st.subheader(f"✏️ Editando: {tarefa['nome']}")
        
        novo_nome = st.text_input("Nome", tarefa['nome'])
        nova_desc = st.text_area("Descrição", tarefa['descricao'] if tarefa['descricao'] else "")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Salvar", help="Salvar alterações"):
                execute_query(
                    "UPDATE tarefas SET nome=?, descricao=? WHERE id=?",
                    (novo_nome, nova_desc, tarefa_id)
                )
                execute_query(
                    "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                    (tarefa_id, "Tarefa editada")
                )
                st.session_state.task_id = None
                st.rerun()
        with c2:
            if st.button("❌ Fechar", help="Fechar sem salvar"):
                st.session_state.task_id = None
                st.rerun()
        
        novo_status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluído"], 
                                   index=["Pendente", "Em andamento", "Concluído"].index(tarefa['status']))
        
        if st.button("🔄 Atualizar status", help="Alterar o status da tarefa"):
            execute_query(
                "UPDATE tarefas SET status=? WHERE id=?",
                (novo_status, tarefa_id)
            )
            execute_query(
                "INSERT INTO historico (tarefa_id, acao) VALUES (?, ?)",
                (tarefa_id, f"Status alterado para: {novo_status}")
            )
            st.rerun()
    else:
        st.warning("⚠️ Tarefa não encontrada!")
        st.session_state.task_id = None
        st.rerun()


# EXPORTAR DADOS

st.divider()
st.subheader("📥 Exportar Dados")

c1, c2 = st.columns(2)

with c1:
    if st.button("📊 Exportar Tarefas", help="Exportar todas as tarefas para Excel"):
        df_export = query_to_df("SELECT * FROM tarefas ORDER BY status, data_criacao")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Tarefas", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar", data=output, 
                          file_name=f"tarefas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with c2:
    if st.button("📜 Exportar Histórico", help="Exportar histórico de ações para Excel"):
        df_hist = query_to_df("SELECT * FROM historico ORDER BY data DESC")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_hist.to_excel(writer, sheet_name="Historico", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar", data=output,
                          file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")