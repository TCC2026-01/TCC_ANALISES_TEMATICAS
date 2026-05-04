# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
from utilitarios import simplificar_topico, extract_keywords, metric_bold

def exibir(df):
    st.subheader("Análise Temática — Artigos Científicos")

    df_temas = df.groupby('nome_topico').agg(
        qtd=('titulo', 'count'),
        qtd_instituicoes=('instituicao', 'nunique')
    ).reset_index()
    df_temas.columns = ['tema', 'qtd', 'qtd_instituicoes']
    df_temas = df_temas.sort_values('qtd', ascending=False)
    df_temas['tema_simples'] = df_temas['tema'].apply(simplificar_topico)

    col1, col2 = st.columns(2)
    with col1:
        tema_top = df_temas.iloc[0]['tema_simples'] if not df_temas.empty else 'N/A'
        metric_bold("Tema Mais Frequente", tema_top)
    with col2:
        metric_bold("Média Artigos/Tema", f"{df_temas['qtd'].mean():.1f}")

    st.markdown("---")

    st.subheader("Evolução Temporal dos Principais Temas")
    top_temas = df_temas.head(5)['tema'].tolist()
    df_tempo = df[df['nome_topico'].isin(top_temas)].groupby(['ano', 'nome_topico']).size().reset_index(name='count')
    df_tempo['tema_simples'] = df_tempo['nome_topico'].apply(simplificar_topico)
    fig = px.line(df_tempo, x='ano', y='count', color='tema_simples', markers=True,
                  labels={'count': 'Artigos', 'ano': 'Ano', 'tema_simples': 'Tema'})
    fig.update_layout(height=400, hovermode='x unified')
    st.plotly_chart(fig, config={'responsive': True}, key="atm_1")

    st.markdown("---")

    st.subheader("Análise por Tema")
    tema_sel = st.selectbox("Selecione um tema", options=df_temas['tema'].tolist(), format_func=simplificar_topico, key='artigos_tema_select')
    if tema_sel:
        df_det = df[df['nome_topico'] == tema_sel]
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Artigos", len(df_det))
        with col_b:
            st.metric("Instituições", df_det['instituicao'].nunique())

        st.write("**Top Palavras-Chave:**")
        keywords = extract_keywords(df_det['resumo_processado'], top_n=10)
        col1, col2 = st.columns(2)
        metade = len(keywords) // 2
        with col1:
            for word, freq in keywords[:metade]:
                st.write(f"• {word}: {freq} ocorrências")
        with col2:
            for word, freq in keywords[metade:]:
                st.write(f"• {word}: {freq} ocorrências")

        st.markdown("---")
        st.subheader("Top Veículos neste Tema")
        if df_det['veiculo'].notna().any():
            top_v = df_det['veiculo'].dropna().value_counts().head(8).reset_index()
            top_v.columns = ['Veículo', 'Artigos']
            fig2 = px.bar(top_v, x='Artigos', y='Veículo', orientation='h',
                          labels={'Artigos': 'Quantidade', 'Veículo': ''})
            fig2.update_layout(height=350, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig2, config={'responsive': True}, key="atm_2")

    st.markdown("---")
    st.subheader("Mapa de Calor: Temas × Instituições")
    top_inst_heatmap = df['instituicao'].value_counts().head(6).index.tolist()
    top_temas_heatmap = df_temas.head(6)['tema'].tolist()
    df_heatmap = df[(df['instituicao'].isin(top_inst_heatmap)) & (df['nome_topico'].isin(top_temas_heatmap))]
    if not df_heatmap.empty:
        pivot_table = df_heatmap.pivot_table(index='nome_topico', columns='instituicao', values='titulo', aggfunc='count', fill_value=0)
        pivot_table.index = pivot_table.index.map(simplificar_topico)
        fig3 = px.imshow(pivot_table, labels=dict(x="Instituição", y="Tema", color="Artigos"), aspect='auto')
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, config={'responsive': True}, key="atm_3")
    else:
        st.info("Dados insuficientes para gerar o mapa de calor.")