# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import gdown

DRIVE_IDS = {
    "tccs_dashboard.parquet":     "17VfHJdaBYLd1WHOWe9LuGhN19X-w6Bgb",
    "projetos_dashboard.parquet": "1w3nSAvZhi7HpVquX1A4b2RwgHIBcON7v",
    "artigos_dashboard.parquet":  "1X9GfMMfpugyYgwgck_VY9TPplHIPMViy",
}

# =========================
# CONFIGURAÇÃO DE COLUNAS
# =========================
COLUNAS_OBRIGATORIAS = {
    "tccs_dashboard.parquet": [
        'titulo', 'autores', 'ano', 'instituicao',
        'resumo', 'resumo_processado',
        'curso', 'nome_topico', 'orientador',
        'curso_unificado', 'tipo'
    ],
    "artigos_dashboard.parquet": [
        'titulo', 'autores', 'ano', 'instituicao',
        'resumo', 'resumo_processado',
        'nome_topico', 'orientador', 'tipo'
    ],
    "projetos_dashboard.parquet": [
        'titulo', 'autores', 'instituicao',
        'resumo', 'resumo_processado',
        'nome_topico', 'tipo',
        'ano_inicio', 'ano_fim'
    ],
}


# =========================
# FUNÇÕES AUXILIARES
# =========================
def garantir_colunas(df, nome_arquivo):
    """Garante que todas as colunas obrigatórias existam."""
    required_cols = COLUNAS_OBRIGATORIAS.get(nome_arquivo, [])
    for col in required_cols:
        if col not in df.columns:
            if col in ["ano", "ano_inicio", "ano_fim"]:
                df[col] = None
            else:
                df[col] = "Não informado"
    return df


def normalizar_campos(df):
    """Normaliza campos críticos para evitar erro no dashboard."""
    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    if "ano_inicio" in df.columns:
        df["ano_inicio"] = pd.to_numeric(df["ano_inicio"], errors="coerce")
    if "ano_fim" in df.columns:
        df["ano_fim"] = pd.to_numeric(df["ano_fim"], errors="coerce")

    colunas_texto = [
        "titulo", "autores", "instituicao",
        "resumo", "resumo_processado",
        "nome_topico", "orientador",
        "curso", "curso_unificado", "tipo"
    ]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).fillna("Não informado").str.strip()
    return df


def garantir_curso_unificado(df):
    """Garante consistência do campo curso_unificado."""
    if "curso_unificado" not in df.columns:
        if "curso" in df.columns:
            df["curso_unificado"] = df["curso"]
        else:
            df["curso_unificado"] = "Não informado"
    df["curso_unificado"] = df["curso_unificado"].replace("", "Não informado")
    return df


# =========================
# FUNÇÃO PRINCIPAL
# =========================
@st.cache_data
def carregar_dados(nome_arquivo="tccs_dashboard.parquet"):
    try:
        BASE_DIR = os.path.dirname(__file__)
        file_path = os.path.join(BASE_DIR, nome_arquivo)

        # -------------------------
        # DOWNLOAD SE NECESSÁRIO
        # -------------------------
        if not os.path.exists(file_path):
            file_id = DRIVE_IDS.get(nome_arquivo)
            if not file_id:
                st.error(f"ID não configurado para '{nome_arquivo}'.")
                st.stop()
            with st.spinner(f"⬇️ Baixando {nome_arquivo}..."):
                url = f"https://drive.google.com/uc?id={file_id}"
                gdown.download(url, file_path, quiet=False)

        if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:
            st.error(f"Falha ao baixar '{nome_arquivo}'. Tente recarregar a página.")
            st.stop()

        # -------------------------
        # LEITURA
        # -------------------------
        df = pd.read_parquet(file_path)

        if df.empty:
            st.warning(f"Arquivo '{nome_arquivo}' está vazio.")
            return pd.DataFrame()

        # -------------------------
        # GARANTIR COLUNAS
        # -------------------------
        df = garantir_colunas(df, nome_arquivo)

        # -------------------------
        # NORMALIZAÇÃO
        # -------------------------
        df = normalizar_campos(df)

        # -------------------------
        # REGRAS ESPECÍFICAS
        # -------------------------
        if nome_arquivo == "tccs_dashboard.parquet":
            df = garantir_curso_unificado(df)
            df = df.dropna(subset=["ano"])
            if not df.empty:
                df["ano"] = df["ano"].astype(int)

        elif nome_arquivo == "artigos_dashboard.parquet":
            df = df.dropna(subset=["ano"])
            if not df.empty:
                df["ano"] = df["ano"].astype(int)

        elif nome_arquivo == "projetos_dashboard.parquet":
            pass

        # -------------------------
        # RESULTADO FINAL
        # -------------------------
        return df

    except Exception as e:
        import traceback
        st.error(f"Erro ao carregar '{nome_arquivo}': {e}")
        st.error(traceback.format_exc())
        st.stop()