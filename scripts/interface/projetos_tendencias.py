# -*- coding: utf-8 -*-
import re
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from utilitarios import prever_tendencias, extrair_termos_emergentes, simplificar_topico


def _preparar_temporal(df):
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

    df["ano"] = df["data_inicio"].apply(extrair_ano)
    mask = df["ano"].isna()
    df.loc[mask, "ano"] = df.loc[mask, "data_fim"].apply(extrair_ano)

    return df.dropna(subset=["ano"]).copy()


def exibir(df):
    st.subheader("Análise de Tendências — Projetos Acadêmicos")
    st.info("Identifica temas em ascensão e declínio com base na produção histórica de projetos.")

    df_model = _preparar_temporal(df)
    if df_model.empty:
        st.warning("Não há datas de início/fim suficientes para análise temporal dos projetos.")
        return

    df_model["ano"] = df_model["ano"].astype(int)

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("**Configurações de Análise:**")
    with col2:
        anos_previsao = st.selectbox("Anos para previsão", [2, 3, 4, 5], index=1)

    if st.button("Executar Análise de Tendências", type="primary"):
        with st.spinner("Processando dados e treinando modelos..."):

            st.markdown("---")
            st.subheader("Tendências por Tema")
            df_tend = prever_tendencias(df_model, anos_previsao=anos_previsao)

            if not df_tend.empty:
                df_tend['classificacao'] = df_tend['score_tendencia'].apply(
                    lambda x: 'Alto Crescimento' if x > 2 else
                              ('Crescimento Moderado' if x > 0 else
                               ('Declínio Moderado' if x > -2 else 'Forte Declínio'))
                )
                df_tend['tema_simples'] = df_tend['tema'].apply(simplificar_topico)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Temas em Crescimento", len(df_tend[df_tend['score_tendencia'] > 0]))
                with col2:
                    st.metric("Temas em Declínio", len(df_tend[df_tend['score_tendencia'] < 0]))
                with col3:
                    melhor = df_tend.nlargest(1, 'score_tendencia').iloc[0]['tema_simples']
                    st.metric("Maior Potencial", melhor[:20] + "..." if len(melhor) > 20 else melhor)
                with col4:
                    st.metric("Crescimento Médio", f"{df_tend['percentual_mudanca'].mean():.1f}%")

                top10 = df_tend.nlargest(10, 'score_tendencia').sort_values('score_tendencia', ascending=True)
                colors = ['#00CC96' if x > 2 else '#FFA15A' if x > 0 else '#EF553B' for x in top10['score_tendencia']]
                fig = go.Figure(go.Bar(
                    y=top10['tema_simples'], x=top10['score_tendencia'], orientation='h',
                    marker=dict(color=colors),
                    text=top10['score_tendencia'].round(2), textposition='outside'
                ))
                fig.update_layout(height=500, xaxis_title="Score de Tendência", yaxis_title="", showlegend=False)
                st.plotly_chart(fig, config={'responsive': True}, key="pte_1", use_container_width=True)

                df_display = df_tend[['tema_simples', 'ultimo_valor', 'previsao_media', 'percentual_mudanca', 'classificacao']].copy()
                df_display.columns = ['Tema', 'Projetos Atuais', 'Previsão Média', 'Mudança %', 'Tendência']
                df_display = df_display.sort_values('Mudança %', ascending=False)
                df_display['Projetos Atuais'] = df_display['Projetos Atuais'].round(0).astype(int)
                df_display['Previsão Média'] = df_display['Previsão Média'].round(1)
                df_display['Mudança %'] = df_display['Mudança %'].round(1)
                st.dataframe(df_display, hide_index=True, use_container_width=True, height=400)
            else:
                st.warning("Dados insuficientes para análise de tendências.")

            st.markdown("---")
            st.subheader("Termos Emergentes nos Resumos")
            df_emerg = extrair_termos_emergentes(df_model, top_n=15)
            if not df_emerg.empty:
                col_left, col_right = st.columns(2)
                with col_left:
                    fig2 = px.bar(
                        df_emerg.sort_values('crescimento_pct', ascending=True),
                        x='crescimento_pct', y='termo', orientation='h',
                        labels={'crescimento_pct': 'Crescimento (%)', 'termo': 'Termo'}
                    )
                    fig2.update_layout(height=500, yaxis_title="")
                    st.plotly_chart(fig2, config={'responsive': True}, key="pte_2", use_container_width=True)
                with col_right:
                    df_emerg_disp = df_emerg[['termo', 'freq_antiga', 'freq_recente', 'crescimento_pct']].copy()
                    df_emerg_disp.columns = ['Termo', 'Freq. Antiga', 'Freq. Recente', 'Crescimento %']
                    df_emerg_disp['Crescimento %'] = df_emerg_disp['Crescimento %'].round(1)
                    st.dataframe(df_emerg_disp, hide_index=True, use_container_width=True, height=500)
            else:
                st.warning("Não foi possível identificar termos emergentes.")

            st.markdown("---")
            st.subheader("Previsão de Produção por Tema")
            top5 = df_model['nome_topico'].value_counts().head(5).index.tolist()
            if top5:
                tema_viz = st.selectbox(
                    "Selecione um tema",
                    options=top5,
                    format_func=simplificar_topico,
                    key='projetos_tendencia_select'
                )
                if tema_viz:
                    df_hist = (
                        df_model[df_model['nome_topico'] == tema_viz]
                        .groupby('ano')
                        .size()
                        .reset_index(name='count')
                        .sort_values('ano')
                    )
                    if len(df_hist) >= 2:
                        X = df_hist['ano'].values.reshape(-1, 1)
                        y = df_hist['count'].values
                        model = LinearRegression().fit(X, y)
                        anos_fut = np.array(
                            [df_model['ano'].max() + i for i in range(1, anos_previsao + 1)]
                        ).reshape(-1, 1)
                        prev = np.maximum(model.predict(anos_fut), 0)
                        df_prev = pd.DataFrame({'ano': anos_fut.flatten(), 'count': prev, 'tipo': 'Previsão'})
                        df_hist['tipo'] = 'Histórico'
                        fig3 = px.line(
                            pd.concat([df_hist, df_prev]),
                            x='ano', y='count', color='tipo', markers=True,
                            labels={'count': 'Quantidade de Projetos', 'ano': 'Ano de Início'}
                        )
                        fig3.update_layout(height=400)
                        st.plotly_chart(fig3, config={'responsive': True}, key="pte_3", use_container_width=True)
                    else:
                        st.warning("Dados insuficientes para este tema.")
    else:
        st.info("Clique no botão acima para executar a análise.")
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Regressão Linear**")
            st.write("Análise de tendências temporais por tema")
        with col2:
            st.write("**Análise de Crescimento**")
            st.write("Comparação entre períodos para identificar termos emergentes")
        with col3:
            st.write("**Previsão**")
            st.write("Projeção de projetos para os próximos anos")
