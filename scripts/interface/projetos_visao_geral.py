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

    st.subheader("Visão Geral — Projetos Acadêmicos")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_bold("Total de Projetos", f"{len(df):,}".replace(",", "."))

    with col2:
        metric_bold("Instituições", df['instituicao'].nunique())

    with col3:
        total_autores = (
            df['autores']
            .dropna()
            .astype(str)
            .str.split(',')
            .explode()
            .str.strip()
            .nunique()
        )
        metric_bold("Autores Únicos", f"{total_autores:,}".replace(",", "."))

    with col4:
        projetos_com_periodo = (df['periodo'].astype(str).str.strip() != "").sum()
        metric_bold("Com Período", f"{int(projetos_com_periodo):,}".replace(",", "."))

    st.markdown("---")

    if df['ano_referencia'].notna().any():
        st.subheader("Distribuição por Ano de Início")
        df_ano = (
            df.dropna(subset=['ano_referencia'])
            .groupby('ano_referencia')
            .size()
            .reset_index(name='Projetos')
            .sort_values('ano_referencia')
        )
        fig_ano = px.bar(
            df_ano,
            x='ano_referencia',
            y='Projetos',
            text='Projetos',
            labels={'ano_referencia': 'Ano de Início'}
        )
        fig_ano.update_traces(textposition='outside')
        fig_ano.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_ano, config={'responsive': True}, key="pvg_ano", use_container_width=True)
        st.markdown("---")

    st.subheader("Distribuição por Natureza do Projeto")

    df_nat = df['natureza'].fillna('Não informado').value_counts().reset_index()
    df_nat.columns = ['Natureza', 'Projetos']

    col_nat1, col_nat2 = st.columns(2)

    with col_nat1:
        fig_pizza = px.pie(
            df_nat,
            values='Projetos',
            names='Natureza',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
        fig_pizza.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_pizza, config={'responsive': True}, key="pvg_nat_pizza", use_container_width=True)

    with col_nat2:
        fig_bar = px.bar(
            df_nat,
            x='Natureza',
            y='Projetos',
            color='Natureza',
            color_discrete_sequence=px.colors.qualitative.Bold,
            text='Projetos',
            labels={'Projetos': 'Quantidade', 'Natureza': ''}
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=400, showlegend=False, xaxis_title="", yaxis_title="Quantidade")
        st.plotly_chart(fig_bar, config={'responsive': True}, key="pvg_nat_bar", use_container_width=True)

    st.markdown("---")

    st.subheader("Natureza dos Projetos por Instituição")

    top10_inst = df['instituicao'].value_counts().head(10).index.tolist()
    df_inst_nat = (
        df[df['instituicao'].isin(top10_inst)]
        .groupby(['instituicao', 'natureza'])
        .size()
        .reset_index(name='count')
    )

    fig_empilhado = px.bar(
        df_inst_nat,
        x='instituicao',
        y='count',
        color='natureza',
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={'count': 'Projetos', 'instituicao': 'Instituição', 'natureza': 'Natureza'},
        barmode='stack'
    )
    fig_empilhado.update_layout(height=450, xaxis_tickangle=-30, xaxis_title="", yaxis_title="Quantidade")
    st.plotly_chart(fig_empilhado, config={'responsive': True}, key="pvg_inst_nat", use_container_width=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 5 Instituições")
        top_inst = df['instituicao'].value_counts().head(5).reset_index()
        top_inst.columns = ['Instituição', 'Projetos']
        st.dataframe(top_inst, hide_index=True, use_container_width=True)

    with col2:
        st.subheader("Top 10 Financiadores")
        if 'financiadores' in df.columns and df['financiadores'].notna().any():
            financiadores = (
                df['financiadores']
                .dropna()
                .astype(str)
                .str.split(';')
                .explode()
                .str.strip()
            )
            financiadores = financiadores[financiadores != '']
            if not financiadores.empty:
                top_f = financiadores.value_counts().head(10).reset_index()
                top_f.columns = ['Financiador', 'Projetos']
                st.dataframe(top_f, hide_index=True, use_container_width=True)
            else:
                st.info("Dados de financiadores não disponíveis.")
        else:
            st.info("Campo 'financiadores' não encontrado.")

    st.markdown("---")
    st.subheader("Tabela de Projetos")
    st.markdown(f"**Total exibido:** {len(df):,} registros".replace(",", "."))

    cols = [c for c in [
        'titulo', 'autores', 'periodo', 'instituicao', 'natureza', 'nome_topico', 'financiadores'
    ] if c in df.columns]

    df_exib = df.sort_values('ano_referencia', ascending=False, na_position='last')
    st.dataframe(
        df_exib[cols],
        hide_index=True,
        use_container_width=True
    )
