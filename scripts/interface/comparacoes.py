# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utilitarios import metric_bold


def exibir(df_tcc, df_art, df_proj):
    # st.subheader("Comparações entre TCCs, Artigos e Projetos")

        # ── MÉTRICAS GERAIS ───────────────────────────────────────────────────────
    st.subheader("Visão Geral da Produção")
    col1, col2, col3, col4 = st.columns(4)
    total = len(df_tcc) + len(df_art) + len(df_proj)
    with col1:
        metric_bold("Total Geral", f"{total:,}".replace(",", "."))
    with col2:
        metric_bold("TCCs", f"{len(df_tcc):,}".replace(",", "."))
    with col3:
        metric_bold("Artigos", f"{len(df_art):,}".replace(",", "."))
    with col4:
        metric_bold("Projetos", f"{len(df_proj):,}".replace(",", "."))

    st.markdown("---")
    st.caption("Os filtros globais da barra lateral são aplicados automaticamente em todos os gráficos.")

    st.markdown("---")

    # ── EVOLUÇÃO TEMPORAL ─────────────────────────────────────────────────────
    st.subheader("Evolução Temporal da Produção")
    df_tcc_ano  = df_tcc.groupby('ano').size().reset_index(name='count')
    df_tcc_ano['tipo'] = 'TCCs'
    df_art_ano  = df_art.groupby('ano').size().reset_index(name='count')
    df_art_ano['tipo'] = 'Artigos'
    df_tempo = pd.concat([df_tcc_ano, df_art_ano])
    df_tempo = df_tempo[df_tempo['ano'] >= 1960]
    fig_tempo = px.line(df_tempo, x='ano', y='count', color='tipo', markers=True)
    fig_tempo.update_layout(height=400, hovermode='x unified')
    st.plotly_chart(fig_tempo, config={'responsive': True}, key="cmp_tempo", use_container_width=True)
    st.caption("⚠️ Projetos não possuem dados de ano disponíveis.")

    st.markdown("---")

# ── RANKING DE IFs POR TIPO ───────────────────────────────────────────────
    st.subheader("Ranking de Instituições por Tipo de Produção")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📚 Top 10 — TCCs**")
        top_tcc = df_tcc['instituicao'].value_counts().head(10).reset_index()
        top_tcc.columns = ['Instituição', 'Quantidade']
        fig1 = px.bar(top_tcc, x='Instituição', y='Quantidade',
                      color_discrete_sequence=['#4A90E2'], text='Quantidade')
        fig1.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig1.update_layout(height=400, showlegend=False,
                           xaxis_tickangle=-30, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig1, config={'responsive': True}, key="cmp_rank_tcc", use_container_width=True)

    with col2:
        st.markdown("**🔬 Top 10 — Artigos**")
        top_art = df_art['instituicao'].value_counts().head(10).reset_index()
        top_art.columns = ['Instituição', 'Quantidade']
        fig2 = px.bar(top_art, x='Instituição', y='Quantidade',
                      color_discrete_sequence=['#00CC96'], text='Quantidade')
        fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig2.update_layout(height=400, showlegend=False,
                           xaxis_tickangle=-30, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig2, config={'responsive': True}, key="cmp_rank_art", use_container_width=True)

    with col3:
        st.markdown("**🗂️ Top 10 — Projetos**")
        top_proj = df_proj['instituicao'].value_counts().head(10).reset_index()
        top_proj.columns = ['Instituição', 'Quantidade']
        fig3 = px.bar(top_proj, x='Instituição', y='Quantidade',
                      color_discrete_sequence=['#FFA15A'], text='Quantidade')
        fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig3.update_layout(height=400, showlegend=False,
                           xaxis_tickangle=-30, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig3, config={'responsive': True}, key="cmp_rank_proj", use_container_width=True)

    # ── COMPARAÇÃO POR IF ─────────────────────────────────────────────────────
    st.subheader("Comparação por Instituição")
    st.caption("Top 10 IFs com maior produção de TCCs comparadas nos 3 tipos")

    top_inst_geral = df_tcc['instituicao'].value_counts().head(10).index.tolist()
    df_comp = pd.DataFrame({
        'Instituição': top_inst_geral,
        'TCCs':     [len(df_tcc[df_tcc['instituicao'] == i]) for i in top_inst_geral],
        'Artigos':  [len(df_art[df_art['instituicao'] == i]) for i in top_inst_geral],
        'Projetos': [len(df_proj[df_proj['instituicao'] == i]) for i in top_inst_geral],
    })
    df_comp_melted = df_comp.melt(id_vars='Instituição', var_name='Tipo', value_name='Quantidade')
    fig_comp = px.bar(df_comp_melted, x='Instituição', y='Quantidade', color='Tipo',
                      barmode='group',
                      color_discrete_map={'TCCs': '#4A90E2', 'Artigos': '#00CC96', 'Projetos': '#FFA15A'},
                      labels={'Quantidade': 'Quantidade', 'Instituição': ''},
                      text='Quantidade')
    fig_comp.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_comp.update_layout(height=500, xaxis_tickangle=-30,
                           xaxis_title="", yaxis_title="Quantidade",
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_comp, config={'responsive': True}, key="cmp_por_if", use_container_width=True)