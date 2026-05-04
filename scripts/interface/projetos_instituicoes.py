# -*- coding: utf-8 -*-
import re
import pandas as pd
import streamlit as st
import plotly.express as px
from utilitarios import metric_bold


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

    st.subheader("Análise por Instituição — Projetos Acadêmicos")

    col1, col2 = st.columns(2)
    with col1:
        metric_bold("Total de Instituições", df['instituicao'].nunique())
    with col2:
        top_inst_nome = df['instituicao'].value_counts().index[0] if not df.empty else "N/A"
        metric_bold("Instituição Mais Ativa", top_inst_nome)

    st.markdown("---")

    st.subheader("Ranking de Instituições por Produção")
    top_inst = df['instituicao'].value_counts().reset_index()
    top_inst.columns = ['Instituição', 'Projetos']
    fig = px.bar(
        top_inst.head(15),
        x='Projetos',
        y='Instituição',
        orientation='h',
        labels={'Projetos': 'Quantidade', 'Instituição': ''},
        color='Projetos',
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=500, yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    st.plotly_chart(fig, config={'responsive': True}, key="pin_1", use_container_width=True)

    st.markdown("---")

    st.subheader("Produção por Ano de Início e Instituição")
    top5 = df['instituicao'].value_counts().head(5).index.tolist()
    df_tempo = (
        df[df['instituicao'].isin(top5) & df['ano_referencia'].notna()]
        .groupby(['ano_referencia', 'instituicao'])
        .size()
        .reset_index(name='count')
        .sort_values('ano_referencia')
    )
    if not df_tempo.empty:
        fig2 = px.line(
            df_tempo,
            x='ano_referencia',
            y='count',
            color='instituicao',
            markers=True,
            labels={'count': 'Projetos', 'ano_referencia': 'Ano de Início', 'instituicao': 'Instituição'}
        )
        fig2.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig2, config={'responsive': True}, key="pin_2", use_container_width=True)
    else:
        st.info("Dados temporais insuficientes para este gráfico.")

    st.markdown("---")

    st.subheader("Detalhamento por Instituição")
    inst_sel = st.selectbox("Selecione uma instituição", options=sorted(df['instituicao'].dropna().unique()))
    if inst_sel:
        df_inst = df[df['instituicao'] == inst_sel].copy()
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total de Projetos", len(df_inst))
        with col_b:
            st.metric("Temas", df_inst['nome_topico'].nunique())
        with col_c:
            autores = df_inst['autores'].dropna().astype(str).str.split(',').explode().str.strip().nunique()
            st.metric("Autores Únicos", autores)

        cols = [c for c in ['titulo', 'autores', 'periodo', 'natureza', 'nome_topico'] if c in df.columns]
        df_inst_exib = df_inst.sort_values('ano_referencia', ascending=False, na_position='last')
        st.dataframe(
            df_inst_exib[cols],
            hide_index=True,
            use_container_width=True
        )
