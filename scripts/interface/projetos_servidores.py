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
    return df


def exibir(df):
    df = _preparar_datas(df)

    st.subheader("Análise de Servidores — Projetos Acadêmicos")

    df_serv = df.groupby('autores').agg(
        qtd=('titulo', 'count'),
        tema_principal=('nome_topico', lambda x: x.mode()[0] if not x.mode().empty else 'N/A'),
        instituicao=('instituicao', lambda x: x.mode()[0] if not x.mode().empty else 'N/A'),
        ano_inicio=('ano_referencia', 'min'),
        ano_fim=('ano_referencia', 'max')
    ).reset_index()
    df_serv.columns = ['servidor', 'qtd', 'tema_principal', 'instituicao', 'ano_inicio', 'ano_fim']
    df_serv = df_serv.sort_values('qtd', ascending=False)

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_bold("Total de Servidores", len(df_serv))
    with col2:
        metric_bold("Média Projetos/Servidor", f"{df_serv['qtd'].mean():.1f}" if not df_serv.empty else "0.0")
    with col3:
        metric_bold("Máximo de Projetos", int(df_serv['qtd'].max()) if not df_serv.empty else 0)

    st.markdown("---")
    st.subheader("Top 10 Servidores por Natureza de Projeto")

    naturezas = {
        'PESQUISA': ('Pesquisa', '#2C5F8A'),
        'EXTENSAO': ('Extensão', '#1A7A5E'),
        'ENSINO': ('Ensino', '#B85C00'),
        'DESENVOLVIMENTO': ('Desenvolvimento', '#7B2D8B'),
        'OUTRA': ('Outra', '#8B1A1A'),
    }

    col1, col2 = st.columns(2)
    for nat, col in [('PESQUISA', col1), ('EXTENSAO', col2)]:
        label, cor = naturezas[nat]
        df_nat = df[df['natureza'] == nat]
        if df_nat.empty:
            continue
        top_nat = df_nat['autores'].dropna().value_counts().head(10).reset_index()
        top_nat.columns = ['Servidor', 'Projetos']
        with col:
            st.markdown(f"**{label}**")
            fig = px.bar(top_nat, x='Servidor', y='Projetos', color_discrete_sequence=[cor], text='Projetos')
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=380, showlegend=False, xaxis_tickangle=-30, xaxis_title="", yaxis_title="Projetos")
            st.plotly_chart(fig, config={'responsive': True}, key=f"proj_srv_nat_{nat}", use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)
    for nat, col in [('ENSINO', col3), ('DESENVOLVIMENTO', col4)]:
        label, cor = naturezas[nat]
        df_nat = df[df['natureza'] == nat]
        if df_nat.empty:
            continue
        top_nat = df_nat['autores'].dropna().value_counts().head(10).reset_index()
        top_nat.columns = ['Servidor', 'Projetos']
        with col:
            st.markdown(f"**{label}**")
            fig = px.bar(top_nat, x='Servidor', y='Projetos', color_discrete_sequence=[cor], text='Projetos')
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=380, showlegend=False, xaxis_tickangle=-30, xaxis_title="", yaxis_title="Projetos")
            st.plotly_chart(fig, config={'responsive': True}, key=f"proj_srv_nat_{nat}", use_container_width=True)

    st.markdown("---")

    col5, col6 = st.columns(2)
    df_nat = df[df['natureza'] == 'OUTRA']
    if not df_nat.empty:
        top_nat = df_nat['autores'].dropna().value_counts().head(10).reset_index()
        top_nat.columns = ['Servidor', 'Projetos']
        with col5:
            st.markdown("**Outra**")
            fig = px.bar(top_nat, x='Servidor', y='Projetos', color_discrete_sequence=['#8B1A1A'], text='Projetos')
            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=380, showlegend=False, xaxis_tickangle=-30, xaxis_title="", yaxis_title="Projetos")
            st.plotly_chart(fig, config={'responsive': True}, key="proj_srv_nat_OUTRA", use_container_width=True)

    st.markdown("---")
    st.subheader("Ranking Completo de Servidores")

    nat_pivot = df.groupby(['autores', 'natureza']).size().unstack(fill_value=0)
    nat_pivot.columns = [c.capitalize() for c in nat_pivot.columns]
    nat_pivot = nat_pivot.reset_index()

    df_display = df_serv[['servidor', 'qtd', 'instituicao', 'ano_inicio', 'ano_fim']].copy()
    df_display['autores'] = df_display['servidor']

    df_final = df_display.merge(nat_pivot, on='autores', how='left')
    df_final = df_final.drop(columns=['autores'])
    df_final = df_final.rename(columns={
        'servidor': 'Servidor',
        'qtd': 'Total',
        'instituicao': 'Instituição',
        'ano_inicio': 'Primeiro Ano',
        'ano_fim': 'Último Ano'
    })

    st.dataframe(df_final, hide_index=True, use_container_width=True, height=400)
