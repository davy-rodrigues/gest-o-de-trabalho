import streamlit as st
import pandas as pd
from database import conectar, criar_tabela
from datetime import datetime
import io

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
criar_tabela()
conn = conectar()
cursor = conn.cursor()

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0E0E11, #1A1A2E);
}
.card {
    background: linear-gradient(145deg, #1A1A2E, #16213E);
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
}
.titulo {
    font-size: 18px;
    font-weight: bold;
    color: #BB86FC;
}
.desc {
    font-size: 13px;
    color: #CFCFCF;
}
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: bold;
    margin-top: 5px;
}
.status-pendente { background: #FF6B6B; color: white; }
.status-andamento { background: #FFD93D; color: #333; }
.status-concluido { background: #6BCB77; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🥸 Gestão Inteligente de Pendências")

# =========================
# NOVA TAREFA
# =========================
with st.form("nova_tarefa"):
    nome = st.text_input("Nome da pendência")
    descricao = st.text_area("Descrição")

    if st.form_submit_button("➕ Adicionar"):
        if nome.strip():
            cursor.execute(
                "INSERT INTO tarefas (nome, status, descricao) VALUES (?, ?, ?)",
                (nome.strip(), "Pendente", descricao.strip())
            )
            conn.commit()
            st.success("Pendência criada!")
            st.rerun()
        else:
            st.warning("Nome não pode ser vazio")

# =========================
# IMPORTAR EXCEL INTELIGENTE
# =========================
st.divider()
st.subheader("📤 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

if arquivo:
    df_import = pd.read_excel(arquivo)
    
    # Mostra as colunas originais para debug
    st.write("**Colunas encontradas no arquivo:**", list(df_import.columns))
    
    # NORMALIZA COLUNAS
    df_import.columns = (
        df_import.columns
        .str.strip()
        .str.lower()
        .str.replace("ç", "c")
        .str.replace("ã", "a")
        .str.replace("á", "a")
        .str.replace("é", "e")
        .str.replace("í", "i")
        .str.replace("ó", "o")
        .str.replace("ú", "u")
        .str.replace("/", "")
        .str.replace(" ", "")
    )
    
    st.dataframe(df_import)

    if st.button("📋 Importar pendências automaticamente"):
        inseridos_pendente = 0
        inseridos_andamento = 0
        inseridos_concluido = 0
        ignorados_excluidos = 0

        for _, row in df_import.iterrows():
            # Tenta identificar as colunas comuns
            nome = ""
            descricao = ""
            status_raw = ""
            
            # Procura por coluna de nome/título
            for col in df_import.columns:
                if any(palavra in col for palavra in ['nome', 'titulo', 'tarefa', 'categoria', 'atividade']):
                    nome = str(row.get(col, "")).strip()
                    break
            
            # Procura por coluna de descrição
            for col in df_import.columns:
                if any(palavra in col for palavra in ['descricao', 'desc', 'detalhe', 'obs']):
                    descricao = str(row.get(col, "")).strip()
                    break
            
            # Procura por coluna de status
            for col in df_import.columns:
                if any(palavra in col for palavra in ['status', 'situacao', 'estado']):
                    status_raw = str(row.get(col, "")).strip().lower()
                    break
            
            # Se não encontrou coluna específica, tenta usar os valores diretamente
            if not nome:
                # Pega o primeiro valor não vazio da linha
                for col in df_import.columns:
                    valor = str(row.get(col, "")).strip()
                    if valor and valor != "nan":
                        nome = valor
                        break
            
            # 🔥 INTELIGÊNCIA DE STATUS (identifica pendente, andamento, concluído, excluído)
            status = "Pendente"  # Status padrão
            
            if status_raw:
                status_raw = status_raw.replace(" ", "").replace("_", "").replace("-", "")
                
                if "pendente" in status_raw or "aberto" in status_raw or "ativo" in status_raw:
                    status = "Pendente"
                    inseridos_pendente += 1
                elif "andamento" in status_raw or "progresso" in status_raw or "fazendo" in status_raw:
                    status = "Em andamento"
                    inseridos_andamento += 1
                elif "conclu" in status_raw or "finalizado" in status_raw or "feito" in status_raw or "completo" in status_raw:
                    status = "Concluído"
                    inseridos_concluido += 1
                elif "exclu" in status_raw or "deletado" in status_raw or "removido" in status_raw:
                    ignorados_excluidos += 1
                    continue  # 👈 IGNORA tarefas excluídas
                else:
                    status = "Pendente"
                    inseridos_pendente += 1
            else:
                # Se não tem coluna de status, tenta identificar pelo contexto
                if any(palavra in nome.lower() for palavra in ['pendente', 'aberto', 'ativo']):
                    status = "Pendente"
                    inseridos_pendente += 1
                elif any(palavra in nome.lower() for palavra in ['andamento', 'progresso']):
                    status = "Em andamento"
                    inseridos_andamento += 1
                elif any(palavra in nome.lower() for palavra in ['conclu', 'finalizado', 'feito']):
                    status = "Concluído"
                    inseridos_concluido += 1
                elif any(palavra in nome.lower() for palavra in ['exclu', 'deletado']):
                    ignorados_excluidos += 1
                    continue
                else:
                    status = "Pendente"
                    inseridos_pendente += 1

            if not nome or nome == "nan":
                continue

            # Prepara descrição completa com metadados
            descricao_completa = descricao if descricao and descricao != "nan" else "Sem descrição detalhada"
            
            # Adiciona informações extras se existirem
            info_extra = []
            for col in df_import.columns:
                valor = row.get(col, "")
                if valor and str(valor) != "nan" and col not in ['nome', 'descricao', 'status', 'titulo', 'categoria', 'atividade']:
                    info_extra.append(f"📌 {col}: {valor}")
            
            if info_extra:
                descricao_completa += "\n\n" + "\n".join(info_extra)

            # Insere no banco de dados
            cursor.execute(
                "INSERT INTO tarefas (nome, status, descricao) VALUES (?, ?, ?)",
                (nome, status, descricao_completa)
            )

            tarefa_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
                (
                    tarefa_id,
                    f"Importado via Excel (Status: {status})",
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                )
            )

        conn.commit()
        
        # Mostra resumo da importação
        st.success(f"""
        ✅ Importação concluída!
        - 📌 Pendentes: {inseridos_pendente}
        - ⚙️ Em andamento: {inseridos_andamento}
        - ✅ Concluídos: {inseridos_concluido}
        - 🗑️ Excluídos ignorados: {ignorados_excluidos}
        """)
        st.rerun()

# =========================
# BUSCAR DADOS
# =========================
df = pd.read_sql("SELECT * FROM tarefas ORDER BY id DESC", conn)

# Mostra estatísticas
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
            # Mostra o cartão da tarefa
            st.markdown(f"""
            <div class="card">
                <div class="titulo">📋 {t['nome']}</div>
                <div class="desc">{t['descricao'][:100]}...</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
            
            with col_btn1:
                if st.button("✏️ Editar", key=f"edit_{status}_{t['id']}"):
                    st.session_state["task_id"] = t["id"]
            
            with col_btn2:
                if status != "Concluído":
                    if st.button("✅ Concluir", key=f"complete_{t['id']}"):
                        cursor.execute("UPDATE tarefas SET status='Concluído' WHERE id=?", (t['id'],))
                        cursor.execute(
                            "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
                            (t['id'], "Tarefa concluída", datetime.now().strftime("%Y-%m-%d %H:%M"))
                        )
                        conn.commit()
                        st.success("Tarefa concluída!")
                        st.rerun()
            
            with col_btn3:
                # Botão de excluir permanente
                if st.button("🗑️ Excluir", key=f"delete_{t['id']}"):
                    # Move para histórico antes de excluir
                    cursor.execute(
                        "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
                        (t['id'], f"Tarefa excluída permanentemente - Status anterior: {t['status']}", 
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                    cursor.execute("DELETE FROM tarefas WHERE id=?", (t['id'],))
                    conn.commit()
                    st.success("Tarefa excluída permanentemente!")
                    st.rerun()
            
            st.markdown("---")

# Renderiza as três colunas
render_coluna("Pendente", col1, "🔴")
render_coluna("Em andamento", col2, "🟡")
render_coluna("Concluído", col3, "🟢")

# =========================
# GERENCIAR TAREFAS EXCLUÍDAS (Histórico)
# =========================
st.divider()
with st.expander("🗑️ Gerenciar Tarefas Excluídas (Histórico)"):
    historico_df = pd.read_sql("SELECT * FROM historico ORDER BY data DESC", conn)
    
    if len(historico_df) > 0:
        st.dataframe(historico_df)
        
        if st.button("Limpar histórico completo"):
            cursor.execute("DELETE FROM historico")
            conn.commit()
            st.success("Histórico limpo!")
            st.rerun()
    else:
        st.info("Nenhuma tarefa no histórico")

# =========================
# DETALHE DA TAREFA
# =========================
if "task_id" in st.session_state:
    tarefa_id = st.session_state["task_id"]
    tarefa = pd.read_sql(f"SELECT * FROM tarefas WHERE id={tarefa_id}", conn)
    
    if len(tarefa) > 0:
        tarefa = tarefa.iloc[0]

        st.divider()
        st.subheader(f"✏️ Editando: {tarefa['nome']}")

        novo_nome = st.text_input("Nome", tarefa["nome"])
        nova_desc = st.text_area("Descrição", tarefa["descricao"])

        col_edit1, col_edit2 = st.columns(2)
        
        with col_edit1:
            if st.button("💾 Salvar edição"):
                cursor.execute(
                    "UPDATE tarefas SET nome=?, descricao=? WHERE id=?",
                    (novo_nome.strip(), nova_desc.strip(), tarefa_id)
                )
                cursor.execute(
                    "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
                    (tarefa_id, "Tarefa editada", datetime.now().strftime("%Y-%m-%d %H:%M"))
                )
                conn.commit()
                st.success("Atualizado!")
                st.rerun()
        
        with col_edit2:
            if st.button("❌ Fechar edição"):
                del st.session_state["task_id"]
                st.rerun()

        novo_status = st.selectbox(
            "Status",
            ["Pendente", "Em andamento", "Concluído"],
            index=["Pendente", "Em andamento", "Concluído"].index(tarefa["status"])
        )

        if st.button("🔄 Atualizar status"):
            cursor.execute(
                "UPDATE tarefas SET status=? WHERE id=?",
                (novo_status, tarefa_id)
            )
            cursor.execute(
                "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
                (tarefa_id, f"Status alterado para: {novo_status}", datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            conn.commit()
            st.success("Status atualizado!")
            st.rerun()
    else:
        st.warning("Tarefa não encontrada!")
        del st.session_state["task_id"]
        st.rerun()

# =========================
# EXPORTAR DADOS
# =========================
st.divider()
st.subheader("📥 Exportar Dados")

col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("📊 Exportar Tarefas Ativas"):
        tarefas_df = pd.read_sql("SELECT * FROM tarefas ORDER BY status, id", conn)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            tarefas_df.to_excel(writer, sheet_name="Tarefas_Ativas", index=False)
        
        output.seek(0)
        
        st.download_button(
            label="⬇️ Baixar Tarefas Ativas",
            data=output,
            file_name=f"tarefas_ativas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with col_export2:
    if st.button("📜 Exportar Histórico Completo"):
        historico_completo = pd.read_sql("SELECT * FROM historico ORDER BY data DESC", conn)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            historico_completo.to_excel(writer, sheet_name="Historico_Completo", index=False)
        
        output.seek(0)
        
        st.download_button(
            label="⬇️ Baixar Histórico",
            data=output,
            file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Fecha conexão
# Nota: Não fechamos aqui porque o Streamlit mantém a conexão aberta