import streamlit as st
import pandas as pd
from database import conectar, criar_tabela
from datetime import datetime
import io

# CONFIG
st.set_page_config(layout="wide")
criar_tabela()
conn = conectar()
cursor = conn.cursor()

# 🎨 CSS PROFISSIONAL
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
    box-shadow: 0px 0px 15px rgba(187,134,252,0.15);
}
.card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0px 0px 25px rgba(187,134,252,0.4);
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
.stButton > button {
    border-radius: 10px;
    background: linear-gradient(90deg, #BB86FC, #00C896);
    color: white;
    border: none;
    transition: 0.3s;
}
.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 10px #00C896;
}
textarea, input {
    border-radius: 8px !important;
}
.history-card {
    background: #121222;
    padding: 10px;
    border-left: 4px solid #00C896;
    border-radius: 8px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Gestão Inteligente de Pendências")

# ---------------------------
# NOVA TAREFA
# ---------------------------
with st.form("nova_tarefa"):
    nome = st.text_input("Nome da pendência")
    descricao = st.text_area("Descrição")

    if st.form_submit_button("➕ Adicionar"):
        cursor.execute(
            "INSERT INTO tarefas (nome, status, descricao) VALUES (?, ?, ?)",
            (nome, "Pendente", descricao)
        )
        conn.commit()
        st.success("Pendência criada!")

# ---------------------------
# BUSCAR DADOS
# ---------------------------
df = pd.read_sql("SELECT * FROM tarefas", conn)

# ---------------------------
# KANBAN
# ---------------------------
col1, col2, col3 = st.columns(3)

def render_coluna(status, coluna):
    with coluna:
        st.subheader(status)
        tarefas = df[df["status"] == status]

        for _, t in tarefas.iterrows():
            st.markdown(f"""
            <div class="card">
                <div class="titulo">{t['nome']}</div>
                <div class="desc">{t['descricao'][:80]}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Abrir", key=f"{status}{t['id']}"):
                st.session_state["task_id"] = t["id"]

render_coluna("Pendente", col1)
render_coluna("Em andamento", col2)
render_coluna("Concluído", col3)

# ---------------------------
# DETALHE DA TAREFA
# ---------------------------
if "task_id" in st.session_state:
    tarefa_id = st.session_state["task_id"]
    tarefa = pd.read_sql(f"SELECT * FROM tarefas WHERE id={tarefa_id}", conn).iloc[0]

    st.divider()
    st.subheader(f"📌 {tarefa['nome']}")

    novo_nome = st.text_input("Nome", tarefa["nome"])
    nova_desc = st.text_area("Descrição", tarefa["descricao"])

    if st.button("💾 Salvar edição"):
        cursor.execute(
            "UPDATE tarefas SET nome=?, descricao=? WHERE id=?",
            (novo_nome, nova_desc, tarefa_id)
        )
        conn.commit()
        st.success("Atualizado!")
        st.rerun()

    novo_status = st.selectbox(
        "Status",
        ["Pendente", "Em andamento", "Concluído"],
        index=["Pendente", "Em andamento", "Concluído"].index(tarefa["status"])
    )

    if st.button("Atualizar status"):
        cursor.execute(
            "UPDATE tarefas SET status=? WHERE id=?",
            (novo_status, tarefa_id)
        )
        conn.commit()
        st.success("Status atualizado!")
        st.rerun()

    nova_acao = st.text_area("O que foi feito")

    if st.button("💾 Salvar atividade"):
        cursor.execute(
            "INSERT INTO historico (tarefa_id, acao, data) VALUES (?, ?, ?)",
            (tarefa_id, nova_acao, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        st.success("Atividade registrada!")
        st.rerun()

    historico = pd.read_sql(
        f"SELECT * FROM historico WHERE tarefa_id={tarefa_id} ORDER BY data DESC",
        conn
    )

    for _, h in historico.iterrows():
        st.markdown(f"""
        <div class="history-card">
            <b>{h['data']}</b><br>
            {h['acao']}
        </div>
        """, unsafe_allow_html=True)

    if st.button("🗑️ Excluir pendência"):
        cursor.execute("DELETE FROM tarefas WHERE id=?", (tarefa_id,))
        cursor.execute("DELETE FROM historico WHERE tarefa_id=?", (tarefa_id,))
        conn.commit()
        st.success("Pendência excluída!")
        del st.session_state["task_id"]
        st.rerun()

# ---------------------------
# EXPORTAR EXCEL (DOWNLOAD REAL)
# ---------------------------
st.divider()
st.subheader("📥 Exportar Excel")

tarefas_df = pd.read_sql("SELECT * FROM tarefas", conn)
historico_df = pd.read_sql("SELECT * FROM historico", conn)

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    tarefas_df.to_excel(writer, sheet_name="Tarefas", index=False)
    historico_df.to_excel(writer, sheet_name="Historico", index=False)

output.seek(0)

st.download_button(
    label="⬇️ Baixar Excel",
    data=output,
    file_name="pendencias.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ---------------------------
# IMPORTAR EXCEL
# ---------------------------
st.divider()
st.subheader("📤 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

if arquivo:
    df_import = pd.read_excel(arquivo)

    st.dataframe(df_import)

    if st.button("Importar pendências"):
        for _, row in df_import.iterrows():
            cursor.execute(
                "INSERT INTO tarefas (nome, status, descricao) VALUES (?, ?, ?)",
                (
                    row.get("nome", ""),
                    row.get("status", "Pendente"),
                    row.get("descricao", "")
                )
            )

        conn.commit()
        st.success("Pendências importadas!")
        st.rerun()
        # ---------------------------
# IMPORTAR EXCEL (CORRIGIDO)
# ---------------------------
st.divider()
st.subheader("📤 Importar Excel")

arquivo = st.file_uploader("Envie um arquivo Excel", type=["xlsx"])

if arquivo:
    df_import = pd.read_excel(arquivo)

    # 🔍 DEBUG (ver colunas reais)
    st.write("Colunas encontradas:", df_import.columns)

    # 🔧 Normalizar colunas
    df_import.columns = (
        df_import.columns
        .str.strip()
        .str.lower()
        .str.replace("ç", "c")
        .str.replace("ã", "a")
        .str.replace("á", "a")
        .str.replace("é", "e")
    )

    # 🔄 Renomear possíveis variações
    df_import = df_import.rename(columns={
        "nome": "nome",
        "descricao": "descricao",
        "descrição": "descricao",
        "status": "status"
    })

    st.write("Pré-visualização:")
    st.dataframe(df_import)

    if st.button("Importar pendências"):
        erros = 0
        inseridos = 0

        for _, row in df_import.iterrows():
            nome = str(row.get("nome", "")).strip()
            descricao = str(row.get("descricao", "")).strip()
            status = str(row.get("status", "Pendente")).strip()

            # 🚫 Evitar registros vazios
            if not nome:
                erros += 1
                continue

            if status not in ["Pendente", "Em andamento", "Concluído"]:
                status = "Pendente"

            cursor.execute(
                "INSERT INTO tarefas (nome, status, descricao) VALUES (?, ?, ?)",
                (nome, status, descricao)
            )
            inseridos += 1

        conn.commit()

        st.success(f"✅ {inseridos} pendências importadas com sucesso!")
        if erros > 0:
            st.warning(f"⚠️ {erros} linhas ignoradas (sem nome)")

        st.rerun()