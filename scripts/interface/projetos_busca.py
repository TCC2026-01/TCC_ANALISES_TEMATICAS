# -*- coding: utf-8 -*-
import re
import pandas as pd
import streamlit as st
from utilitarios import calcular_similaridade


def _preparar_datas(df):
    df = df.copy()

    def extrair_ano(valor):
        if pd.isna(valor):
            return pd.NA
        m = re.search(r"(\d{4})", str(valor))
        return int(m.group(1)) if m else pd.NA

    if "data_inicio" not in df.columns:
        df["data_inicio"] = pd.NA
    if "data_fim" not in df.columns:
        df["data_fim"] = pd.NA

    df["ano_referencia"] = df["data_inicio"].apply(extrair_ano)
    mask = df["ano_referencia"].isna()
    df.loc[mask, "ano_referencia"] = df.loc[mask, "data_fim"].apply(extrair_ano)

    def montar_periodo(row):
        ini = row.get("data_inicio")
        fim = row.get("data_fim")
        if pd.notna(ini) and pd.notna(fim):
            return str(ini) if str(ini) == str(fim) else f"{ini} - {fim}"
        if pd.notna(ini):
            return str(ini)
        if pd.notna(fim):
            return str(fim)
        return ""

    df["periodo"] = df.apply(montar_periodo, axis=1)
    return df


def exibir(df):
    df = _preparar_datas(df)

    st.subheader("Busca de Projetos Acadêmicos")

    col1, col2 = st.columns([3, 1])
    with col1:
        termo = st.text_input("🔍 Buscar por título, autor ou resumo", placeholder="Ex: robótica, sustentabilidade...")
    with col2:
        campo = st.selectbox("Campo", ["Título", "Autor", "Resumo"])

    if termo:
        termo_lower = termo.lower()
        if campo == "Título":
            resultado = df[df['titulo'].astype(str).str.lower().str.contains(termo_lower, na=False)]
        elif campo == "Autor":
            resultado = df[df['autores'].astype(str).str.lower().str.contains(termo_lower, na=False)]
        else:
            resultado = df[df['resumo'].astype(str).str.lower().str.contains(termo_lower, na=False)]

        st.markdown(f"**{len(resultado)} projeto(s) encontrado(s)**")

        if not resultado.empty:
            cols = [c for c in ['titulo', 'autores', 'periodo', 'instituicao', 'natureza', 'nome_topico'] if c in df.columns]
            resultado_exib = resultado.sort_values('ano_referencia', ascending=False, na_position='last')
            st.dataframe(
                resultado_exib[cols],
                hide_index=True,
                use_container_width=True
            )

            st.markdown("---")
            st.subheader("Projetos Similares ao Primeiro Resultado")
            idx = df.index.get_loc(resultado.index[0])
            df_reset = df.reset_index(drop=True)
            similares = calcular_similaridade(df_reset, idx, top_n=5)
            if not similares.empty:
                similares = _preparar_datas(similares)
                cols_sim = [c for c in ['titulo', 'autores', 'periodo', 'instituicao', 'similaridade'] if c in similares.columns]
                similares_exib = similares.sort_values('ano_referencia', ascending=False, na_position='last')
                st.dataframe(similares_exib[cols_sim], hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum projeto encontrado. Tente outro termo.")
    else:
        st.info("Digite um termo acima para buscar projetos.")
        st.markdown("---")
        st.subheader("Projetos Recentes")
        cols = [c for c in ['titulo', 'autores', 'periodo', 'instituicao', 'natureza', 'nome_topico'] if c in df.columns]
        df_exib = df.sort_values('ano_referencia', ascending=False, na_position='last').head(20)
        st.dataframe(
            df_exib[cols],
            hide_index=True,
            use_container_width=True
        )
