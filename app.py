import streamlit as st
import pandas as pd
from database import conectar, criar_tabela
from datetime import datetime
import io
import hashlib

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")
criar_tabela()
conn = conectar()
if conn is None:
    st.stop()
cursor = conn.cursor()

# =========================
# SESSION STATE
# =========================
if 'tarefas_minimizadas' not in st.session_state:
    st.session_state.tarefas_minimizadas = set()
if 'modo_visualizacao' not in st.session_state:
    st.session_state.modo_visualizacao = "expandido"  # expandido ou minimizado

# =========================
# FUNÇÕES AUXILIARES
# =========================
def gerar_id_unico(nome, descricao):
    """Gera um ID único baseado no nome e descrição"""
    conteudo = f"{nome}_{descricao}".encode('utf-8')
    return hashlib.md5(conteudo).hexdigest()[:12]

def toggle_minimizar(tarefa_id):
    """Alterna o estado minimizado de uma tarefa"""
    if tarefa_id in st.session_state.tarefas_minimizadas:
        st.session_state.tarefas_minimizadas.remove(tarefa_id)
    else:
        st.session_state.tarefas_minimizadas.add(tarefa_id)
    st.rerun()

def toggle_todas_minimizar():
    """Minimiza ou expande todas as tarefas"""
    if st.session_state.modo_visualizacao == "expandido":
        st.session_state.modo_visualizacao = "minimizado"
        # Minimiza todas as tarefas atuais
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
.stApp {
    background: linear-gradient(135deg, #0E0E11, #1A1A2E);
}
.card {
    background: linear-gradient(145deg, #1A1A2E, #16213E);
    padding: 15px;
    border-radius: 14px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
}
.card-minimizado {
    background: linear-gradient(145deg, #1A1A2E, #16213E);
    padding: 10px 15px;
    border-radius: 14px;
    margin-bottom: 8px;
    cursor: pointer;
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
.btn-minimizar {
    background: none;
    border: none;
    color: #BB86FC;
    cursor: pointer;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

st.title("🥸 Gestão Inteligente de Pendências")

# Botão para minimizar/expandir todas
col_botoes_top, col_vazio = st.columns([1, 3])
with col_botoes_top:
    if st.session_state.modo_visualizacao == "expandido":
        if st.button("📋 Minimizar Todas as Tarefas", use_container_width=True):
            toggle_todas_minimizar()
    else:
        if st.button("🔍 Expandir Todas as Tarefas", use_container_width=True):
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
            
            # Verifica se o ID já existe
            cursor.execute("SELECT id FROM tarefas WHERE id = %s", (tarefa_id,))
            if cursor.fetchone():
                st.warning("Esta tarefa já existe no sistema!")
            else:
                cursor.execute(
                    "INSERT INTO tarefas (id, nome, status, descricao) VALUES (%s, %s, %s, %s)",
                    (tarefa_id, nome.strip(), "Pendente", descricao.strip())
                )
                conn.commit()
                st.success("Pendência criada!")
                st.rerun()
        else:
            st.warning("Nome não pode ser vazio")

# =========================
# IMPORTAR EXCEL INTELIGENTE COM CONTROLE DE ID
# =========================
st.divider()
st.subheader("📤 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

if arquivo:
    df_import = pd.read_excel(arquivo)
    
    # Mostra as colunas originais para debug
    st.write("**Colunas encontradas no arquivo:**", list(df_import.columns))
    
    # Verifica se existe coluna de ID
    tem_coluna_id = 'id' in [col.lower() for col in df_import.columns]
    if tem_coluna_id:
        st.info("✅ Detectada coluna 'ID' - Usando IDs existentes da planilha")
    
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
        ignorados_duplicados = 0
        atualizados = 0

        for _, row in df_import.iterrows():
            # Tenta identificar ID
            tarefa_id = None
            if tem_coluna_id and 'id' in df_import.columns:
                tarefa_id = str(row.get('id', "")).strip()
                if tarefa_id == "nan" or not tarefa_id:
                    tarefa_id = None
            
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
            
            # Se não encontrou nome, tenta usar valores diretamente
            if not nome or nome == "nan":
                for col in df_import.columns:
                    valor = str(row.get(col, "")).strip()
                    if valor and valor != "nan" and col not in ['id', 'status']:
                        nome = valor
                        break
            
            # Gera ID se não existe
            if not tarefa_id and nome and nome != "nan":
                tarefa_id = gerar_id_unico(nome, descricao)
            
            # Verifica se o ID já existe no banco
            if tarefa_id:
                cursor.execute("SELECT id, nome, status FROM tarefas WHERE id = %s", (tarefa_id,))
                existe = cursor.fetchone()
                
                if existe:
                    # ID existe - verifica se precisa atualizar
                    status_atual = existe[2]
                    
                    # Processa novo status
                    novo_status = status_atual
                    if status_raw:
                        status_raw = status_raw.replace(" ", "").replace("_", "").replace("-", "")
                        
                        if "pendente" in status_raw:
                            novo_status = "Pendente"
                        elif "andamento" in status_raw:
                            novo_status = "Em andamento"
                        elif "conclu" in status_raw:
                            novo_status = "Concluído"
                        elif "exclu" in status_raw:
                            ignorados_excluidos += 1
                            continue
                    
                    # Atualiza se necessário
                    if novo_status != status_atual:
                        cursor.execute(
                            "UPDATE tarefas SET status = %s, descricao = %s WHERE id = %s",
                            (novo_status, descricao, tarefa_id)
                        )
                        cursor.execute(
                            "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                            (tarefa_id, f"Status atualizado via Excel: {status_atual} → {novo_status}")
                        )
                        atualizados += 1
                    
                    ignorados_duplicados += 1
                    continue  # Não insere duplicado
            
            # Processa nova tarefa
            if not nome or nome == "nan":
                continue
            
            # Processa status
            status = "Pendente"
            if status_raw:
                status_raw = status_raw.replace(" ", "").replace("_", "").replace("-", "")
                
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
                    status = "Pendente"
                    inseridos_pendente += 1
            else:
                inseridos_pendente += 1
            
            # Prepara descrição completa
            descricao_completa = descricao if descricao and descricao != "nan" else "Sem descrição detalhada"
            
            info_extra = []
            for col in df_import.columns:
                valor = row.get(col, "")
                if valor and str(valor) != "nan" and col not in ['id', 'nome', 'descricao', 'status', 'titulo', 'categoria', 'atividade']:
                    info_extra.append(f"📌 {col}: {valor}")
            
            if info_extra:
                descricao_completa += "\n\n" + "\n".join(info_extra)
            
            # Insere nova tarefa
            cursor.execute(
                "INSERT INTO tarefas (id, nome, status, descricao) VALUES (%s, %s, %s, %s)",
                (tarefa_id, nome, status, descricao_completa)
            )
            
            cursor.execute(
                "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                (tarefa_id, f"Importado via Excel (Status: {status})")
            )

        conn.commit()
        
        # Mostra resumo da importação
        st.success(f"""
        ✅ Importação concluída!
        - 📌 Novas Pendentes: {inseridos_pendente}
        - ⚙️ Novas Em andamento: {inseridos_andamento}
        - ✅ Novas Concluídas: {inseridos_concluido}
        - 🔄 Atualizadas: {atualizados}
        - ⏭️ Duplicadas ignoradas: {ignorados_duplicados}
        - 🗑️ Excluídas ignoradas: {ignorados_excluidos}
        """)
        st.rerun()

# =========================
# BUSCAR DADOS
# =========================
df = pd.read_sql("SELECT * FROM tarefas ORDER BY data_criacao DESC", conn)

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
            tarefa_id = t['id']
            esta_minimizada = tarefa_id in st.session_state.tarefas_minimizadas
            
            # Verifica se deve mostrar minimizada
            if st.session_state.modo_visualizacao == "minimizado" and not esta_minimizada:
                esta_minimizada = True
                st.session_state.tarefas_minimizadas.add(tarefa_id)
            
            if esta_minimizada:
                # Visualização minimizada
                with st.container():
                    col_min1, col_min2, col_min3 = st.columns([4, 1, 1])
                    with col_min1:
                        if st.button(f"📋 {t['nome'][:50]}", key=f"min_{tarefa_id}", use_container_width=True):
                            toggle_minimizar(tarefa_id)
                    with col_min2:
                        if st.button("✏️", key=f"edit_min_{tarefa_id}"):
                            st.session_state["task_id"] = tarefa_id
                    with col_min3:
                        if st.button("🗑️", key=f"del_min_{tarefa_id}"):
                            cursor.execute(
                                "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                                (tarefa_id, f"Tarefa excluída permanentemente - Status anterior: {t['status']}")
                            )
                            cursor.execute("DELETE FROM tarefas WHERE id = %s", (tarefa_id,))
                            conn.commit()
                            st.success("Tarefa excluída!")
                            st.rerun()
            else:
                # Visualização expandida
                st.markdown(f"""
                <div class="card">
                    <div class="titulo">
                        📋 {t['nome']}
                        <button class="btn-minimizar" onclick="toggle_{tarefa_id}">🔼</button>
                    </div>
                    <div class="desc">{t['descricao'][:100]}...</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 1, 1, 1])
                
                with col_btn1:
                    if st.button("✏️ Editar", key=f"edit_{status}_{tarefa_id}"):
                        st.session_state["task_id"] = tarefa_id
                
                with col_btn2:
                    if status != "Concluído":
                        if st.button("✅ Concluir", key=f"complete_{tarefa_id}"):
                            cursor.execute("UPDATE tarefas SET status='Concluído' WHERE id = %s", (tarefa_id,))
                            cursor.execute(
                                "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                                (tarefa_id, "Tarefa concluída")
                            )
                            conn.commit()
                            st.success("Tarefa concluída!")
                            st.rerun()
                
                with col_btn3:
                    if st.button("📌 Minimizar", key=f"minimize_{tarefa_id}"):
                        toggle_minimizar(tarefa_id)
                
                with col_btn4:
                    if st.button("🗑️ Excluir", key=f"delete_{tarefa_id}"):
                        cursor.execute(
                            "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                            (tarefa_id, f"Tarefa excluída permanentemente - Status anterior: {t['status']}")
                        )
                        cursor.execute("DELETE FROM tarefas WHERE id = %s", (tarefa_id,))
                        conn.commit()
                        st.success("Tarefa excluída!")
                        st.rerun()
            
            st.markdown("---")

# Renderiza as três colunas
render_coluna("Pendente", col1, "🔴")
render_coluna("Em andamento", col2, "🟡")
render_coluna("Concluído", col3, "🟢")

# =========================
# GERENCIAR HISTÓRICO
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
    cursor.execute("SELECT * FROM tarefas WHERE id = %s", (tarefa_id,))
    tarefa_data = cursor.fetchone()
    
    if tarefa_data:
        tarefa = {
            'id': tarefa_data[0],
            'nome': tarefa_data[1],
            'status': tarefa_data[2],
            'descricao': tarefa_data[3]
        }

        st.divider()
        st.subheader(f"✏️ Editando: {tarefa['nome']}")

        novo_nome = st.text_input("Nome", tarefa["nome"])
        nova_desc = st.text_area("Descrição", tarefa["descricao"])

        col_edit1, col_edit2 = st.columns(2)
        
        with col_edit1:
            if st.button("💾 Salvar edição"):
                cursor.execute(
                    "UPDATE tarefas SET nome = %s, descricao = %s WHERE id = %s",
                    (novo_nome.strip(), nova_desc.strip(), tarefa_id)
                )
                cursor.execute(
                    "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                    (tarefa_id, "Tarefa editada")
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
                "UPDATE tarefas SET status = %s WHERE id = %s",
                (novo_status, tarefa_id)
            )
            cursor.execute(
                "INSERT INTO historico (tarefa_id, acao) VALUES (%s, %s)",
                (tarefa_id, f"Status alterado para: {novo_status}")
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
        tarefas_df = pd.read_sql("SELECT * FROM tarefas ORDER BY status, data_criacao", conn)
        
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

# Fecha conexão ao final
# cursor.close()
# conn.close()