import streamlit as st
import pandas as pd
import json
import os

ARQUIVO = "dados.json"

# =========================
# FUNÇÕES
# =========================

def carregar_dados():
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r") as f:
            return json.load(f)
    return []

def salvar_dados(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f, indent=4)

# =========================
# INÍCIO
# =========================

st.set_page_config(page_title="Gestão de Pendências", layout="wide")

st.title("📋 Gestão de Pendências")

dados = carregar_dados()

# =========================
# IMPORTAR EXCEL
# =========================

st.subheader("📥 Importar Planilha")

arquivo = st.file_uploader(
    "Envie um arquivo Excel",
    type=["xlsx"],
    key="upload_excel"  # 🔥 CORREÇÃO AQUI
)

if arquivo:
    try:
        df = pd.read_excel(arquivo)

        st.write("Pré-visualização:")
        st.dataframe(df)

        if st.button("Importar dados", key="btn_importar"):
            for _, linha in df.iterrows():
                nome = str(linha.get("Nome", "")).strip()
                descricao = str(linha.get("Descrição", "")).strip()

                # Evita pendência vazia
                if nome and descricao:
                    dados.append({
                        "id": len(dados) + 1,
                        "nome": nome,
                        "descricao": descricao,
                        "status": "Pendente"
                    })

            salvar_dados(dados)
            st.success("Dados importados com sucesso!")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

# =========================
# LISTAR PENDÊNCIAS
# =========================

st.subheader("📌 Pendências")

for t in dados:
    with st.expander(f"{t['nome']} - {t['status']}"):

        novo_nome = st.text_input(
            "Nome",
            value=t["nome"],
            key=f"nome_{t['id']}"
        )

        nova_desc = st.text_area(
            "Descrição",
            value=t["descricao"],
            key=f"desc_{t['id']}"
        )

        if st.button("💾 Salvar edição", key=f"salvar_{t['id']}"):
            t["nome"] = novo_nome
            t["descricao"] = nova_desc
            salvar_dados(dados)
            st.success("Atualizado!")

        if st.button("Atualizar status", key=f"status_{t['id']}"):
            t["status"] = "Concluído" if t["status"] == "Pendente" else "Pendente"
            salvar_dados(dados)
            st.success("Status atualizado!")

# =========================
# DOWNLOAD
# =========================

st.subheader("📤 Exportar dados")

if dados:
    df_export = pd.DataFrame(dados)
    arquivo_excel = "pendencias.xlsx"
    df_export.to_excel(arquivo_excel, index=False)

    with open(arquivo_excel, "rb") as f:
        st.download_button(
            label="📥 Baixar Excel",
            data=f,
            file_name="pendencias.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )