

import streamlit as st
import pandas as pd
from database import get_engine, criar_tabela
from datetime import datetime
import io
import hashlib
from sqlalchemy import text

# =========================
# CONFIGURAÇÃO INICIAL
# =========================
st.set_page_config(layout="wide")

# Conecta ao banco
criar_tabela()
engine = get_engine()

if engine is None:
    st.error("❌ Não foi possível conectar ao banco. Verifique as configurações.")
    st.stop()

# =========================
# SESSION STATE
# =========================
if 'tarefas_minimizadas' not in st.session_state:
    st.session_state.tarefas_minimizadas = set()
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = "expandido"
if 'task_id' not in st.session_state:
    st.session_state.task_id = None

# =========================
# FUNÇÕES AUXILIARES
# =========================
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
        with engine.connect() as conn:
            df_atual = pd.read_sql("SELECT id FROM tarefas", conn)
            for id_tarefa in df_atual['id'].values:
                st.session_state.tarefas_minimizadas.add(id_tarefa)
    else:
        st.session_state.modo_visualizacao = "expandido"
        st.session_state.tarefas_minimizadas.clear()
    st.rerun()

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0E0E11, #1A1A2E); }
.card {
    background: linear-gradient(145deg, #1A1A2E, #16213E);
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
}
.titulo { font-size: 18px; font-weight: bold; color: #BB86FC; }
.desc { font-size: 13px; color: #CFCFCF; }
</style>
""", unsafe_allow_html=True)

st.title("🥸 Gestão Inteligente de Pendências")

# Botão minimizar/expandir todas
col_botoes_top, _ = st.columns([1, 3])
with col_botoes_top:
    if st.session_state.modo_visualizacao == "expandido":
        if st.button("📋 Minimizar Todas", use_container_width=True):
            toggle_todas_minimizar()
    else:
        if st.button("🔍 Expandir Todas", use_container_width=True):
            toggle_todas_minimizar()

# =========================
# NOVA TAREFA
# =========================
with st.form("nova_tarefa"):
    nome = st.text_input("Nome da pendência")
    descricao = st.text_area("Descrição")

    if st.form_submit_button("➕ Adicionar"):
        if nome.strip():
            tarefa_id = gerar_id_unico(nome.strip(), descricao.strip())
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM tarefas WHERE id = :id"), {"id": tarefa_id})
                if result.fetchone():
                    st.warning("Esta tarefa já existe!")
                else:
                    conn.execute(
                        text("INSERT INTO tarefas (id, nome, status, descricao) VALUES (:id, :nome, :status, :descricao)"),
                        {"id": tarefa_id, "nome": nome.strip(), "status": "Pendente", "descricao": descricao.strip()}
                    )
                    conn.commit()
                    st.success("Pendência criada!")
                    st.rerun()
        else:
            st.warning("Nome não pode ser vazio")

# =========================
# IMPORTAR EXCEL
# =========================
st.divider()
st.subheader("📤 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

if arquivo:
    df_import = pd.read_excel(arquivo)
    st.write("**Colunas encontradas:**", list(df_import.columns))
    
    # Normaliza colunas
    df_import.columns = df_import.columns.str.strip().str.lower()
    st.dataframe(df_import)

    if st.button("📋 Importar pendências"):
        inseridos_pendente = inseridos_andamento = inseridos_concluido = 0
        ignorados_excluidos = ignorados_duplicados = atualizados = 0

        with engine.connect() as conn:
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
                result = conn.execute(text("SELECT id FROM tarefas WHERE id = :id"), {"id": tarefa_id})
                if result.fetchone():
                    ignorados_duplicados += 1
                    continue
                
                # Insere
                conn.execute(
                    text("INSERT INTO tarefas (id, nome, status, descricao) VALUES (:id, :nome, :status, :descricao)"),
                    {"id": tarefa_id, "nome": nome, "status": status, "descricao": descricao or "Sem descrição"}
                )
                conn.execute(
                    text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                    {"id": tarefa_id, "acao": f"Importado via Excel (Status: {status})"}
                )
            
            conn.commit()
        
        st.success(f"""
        ✅ Importação concluída!
        - 📌 Pendentes: {inseridos_pendente}
        - ⚙️ Em andamento: {inseridos_andamento}
        - ✅ Concluídos: {inseridos_concluido}
        - ⏭️ Duplicados ignorados: {ignorados_duplicados}
        - 🗑️ Excluídos ignorados: {ignorados_excluidos}
        """)
        st.rerun()

# =========================
# DASHBOARD
# =========================
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM tarefas ORDER BY data_criacao DESC", conn)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📌 Pendentes", len(df[df['status'] == 'Pendente']))
with col2:
    st.metric("⚙️ Em andamento", len(df[df['status'] == 'Em andamento']))
with col3:
    st.metric("✅ Concluídos", len(df[df['status'] == 'Concluído']))
with col4:
    st.metric("📊 Total", len(df))

# =========================
# KANBAN
# =========================
st.divider()
st.subheader("🎯 Quadro Kanban")

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
                    if st.button(f"📋 {t['nome'][:40]}", key=f"min_{tarefa_id}"):
                        toggle_minimizar(tarefa_id)
                with col_b:
                    if st.button("✏️", key=f"edit_{tarefa_id}"):
                        st.session_state.task_id = tarefa_id
                with col_c:
                    if st.button("🗑️", key=f"del_{tarefa_id}"):
                        with engine.connect() as conn:
                            conn.execute(text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                                       {"id": tarefa_id, "acao": f"Excluída - Status: {t['status']}"})
                            conn.execute(text("DELETE FROM tarefas WHERE id = :id"), {"id": tarefa_id})
                            conn.commit()
                        st.rerun()
            else:
                st.markdown(f"""
                <div class="card">
                    <div class="titulo">📋 {t['nome']}</div>
                    <div class="desc">{t['descricao'][:100] if t['descricao'] else 'Sem descrição'}...</div>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("✏️ Editar", key=f"edit_{status}_{tarefa_id}"):
                        st.session_state.task_id = tarefa_id
                with b2:
                    if status != "Concluído":
                        if st.button("✅ Concluir", key=f"comp_{tarefa_id}"):
                            with engine.connect() as conn:
                                conn.execute(text("UPDATE tarefas SET status='Concluído' WHERE id=:id"), {"id": tarefa_id})
                                conn.execute(text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                                           {"id": tarefa_id, "acao": "Tarefa concluída"})
                                conn.commit()
                            st.rerun()
                with b3:
                    if st.button("📌 Minimizar", key=f"min_{status}_{tarefa_id}"):
                        toggle_minimizar(tarefa_id)
                with b4:
                    if st.button("🗑️ Excluir", key=f"del_{status}_{tarefa_id}"):
                        with engine.connect() as conn:
                            conn.execute(text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                                       {"id": tarefa_id, "acao": f"Excluída - Status: {t['status']}"})
                            conn.execute(text("DELETE FROM tarefas WHERE id=:id"), {"id": tarefa_id})
                            conn.commit()
                        st.rerun()
            
            st.markdown("---")

render_coluna("Pendente", col1, "🔴")
render_coluna("Em andamento", col2, "🟡")
render_coluna("Concluído", col3, "🟢")

# =========================
# DETALHE DA TAREFA
# =========================
if st.session_state.task_id:
    tarefa_id = st.session_state.task_id
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM tarefas WHERE id = :id"), {"id": tarefa_id})
        tarefa = result.fetchone()
    
    if tarefa:
        st.divider()
        st.subheader(f"✏️ Editando: {tarefa[1]}")
        
        novo_nome = st.text_input("Nome", tarefa[1])
        nova_desc = st.text_area("Descrição", tarefa[3] if tarefa[3] else "")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Salvar"):
                with engine.connect() as conn:
                    conn.execute(text("UPDATE tarefas SET nome=:nome, descricao=:desc WHERE id=:id"),
                               {"nome": novo_nome, "desc": nova_desc, "id": tarefa_id})
                    conn.execute(text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                               {"id": tarefa_id, "acao": "Tarefa editada"})
                    conn.commit()
                st.session_state.task_id = None
                st.rerun()
        with c2:
            if st.button("❌ Fechar"):
                st.session_state.task_id = None
                st.rerun()
        
        novo_status = st.selectbox("Status", ["Pendente", "Em andamento", "Concluído"], 
                                   index=["Pendente", "Em andamento", "Concluído"].index(tarefa[2]))
        
        if st.button("🔄 Atualizar status"):
            with engine.connect() as conn:
                conn.execute(text("UPDATE tarefas SET status=:status WHERE id=:id"),
                           {"status": novo_status, "id": tarefa_id})
                conn.execute(text("INSERT INTO historico (tarefa_id, acao) VALUES (:id, :acao)"),
                           {"id": tarefa_id, "acao": f"Status alterado para: {novo_status}"})
                conn.commit()
            st.rerun()
    else:
        st.warning("Tarefa não encontrada!")
        st.session_state.task_id = None
        st.rerun()

# =========================
# EXPORTAR DADOS
# =========================
st.divider()
st.subheader("📥 Exportar Dados")

c1, c2 = st.columns(2)

with c1:
    if st.button("📊 Exportar Tarefas"):
        with engine.connect() as conn:
            df_export = pd.read_sql("SELECT * FROM tarefas ORDER BY status, data_criacao", conn)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_export.to_excel(writer, sheet_name="Tarefas", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar", data=output, 
                          file_name=f"tarefas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with c2:
    if st.button("📜 Exportar Histórico"):
        with engine.connect() as conn:
            df_hist = pd.read_sql("SELECT * FROM historico ORDER BY data DESC", conn)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_hist.to_excel(writer, sheet_name="Historico", index=False)
        output.seek(0)
        st.download_button("⬇️ Baixar", data=output,
                          file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")