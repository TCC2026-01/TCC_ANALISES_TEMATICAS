# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import pandas as pd
from utilitarios import simplificar_topico, metric_bold


def exibir(df):
    st.subheader("Visão Geral")

    # ================================
    # 🔒 PROTEÇÃO (produção real)
    # ================================
    if df is None or df.empty:
        st.warning("Nenhum dado disponível com os filtros aplicados.")
        return

    df = df.copy()

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")

    # ================================
    # 📊 KPIs
    # ================================
    col1, col2, col3 = st.columns(3)

    with col1:
        metric_bold("Total de TCCs", f"{len(df):,}".replace(",", "."))

    with col2:
        metric_bold("Instituições", df['instituicao'].nunique() if 'instituicao' in df else 0)

    with col3:
        metric_bold("Orientadores", df['orientador'].nunique() if 'orientador' in df else 0)

    st.markdown("---")

    # ================================
    # 📈 PRODUÇÃO ANUAL + CRESCIMENTO
    # ================================
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Produção Anual de TCCs")

        if "ano" in df.columns:
            df_ano = df.dropna(subset=["ano"]).groupby('ano').size().reset_index(name='count')
            df_ano = df_ano.sort_values("ano")

            # crescimento %
            df_ano["crescimento_%"] = df_ano["count"].pct_change() * 100

            fig_ano = px.bar(
                df_ano,
                x='ano',
                y='count',
                text='count',
                labels={'count': 'Quantidade', 'ano': 'Ano'},
            )

            fig_ano.update_traces(textposition='outside')

            fig_ano.update_layout(
                height=400,
                showlegend=False,
                yaxis_title="Quantidade de TCCs",
                xaxis_title="Ano"
            )

            st.plotly_chart(fig_ano, config={'responsive': True})

            # crescimento
            if len(df_ano) > 1:
                crescimento_atual = df_ano["crescimento_%"].iloc[-1]
                if pd.notna(crescimento_atual):
                    st.caption(f"📊 Crescimento último ano: {crescimento_atual:.1f}%")
        else:
            st.info("Coluna 'ano' não disponível.")

    # ================================
    # 🧠 TEMAS AGRUPADOS
    # ================================
    with col_right:
        st.subheader("🧠 Distribuição por Tema")

        if "nome_topico" in df.columns:
            df_topicos = df['nome_topico'].value_counts().head(8).reset_index()
            df_topicos.columns = ['tema', 'count']

            df_topicos['tema_simples'] = df_topicos['tema'].apply(simplificar_topico)

            fig_pizza = px.pie(
                df_topicos,
                values='count',
                names='tema_simples',
                hole=0.4
            )

            fig_pizza.update_traces(textinfo='percent+label')

            fig_pizza.update_layout(
                height=400,
                showlegend=True
            )

            st.plotly_chart(fig_pizza, config={'responsive': True})
        else:
            st.info("Coluna 'nome_topico' não disponível.")

    st.markdown("---")

    # ================================
    # 🏫 TOP INSTITUIÇÕES + CURSOS
    # ================================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏫 Top 5 Instituições")

        if "instituicao" in df.columns:
            top_inst = df['instituicao'].value_counts().head(5).reset_index()
            top_inst.columns = ['Instituição', 'Quantidade']

            st.dataframe(
                top_inst,
                hide_index=True,
                width="stretch"
            )
        else:
            st.info("Coluna 'instituicao' não disponível.")

    with col2:
        st.subheader("🎓 Top 5 Cursos")

        if "curso_unificado" in df.columns:
            top_cursos = df['curso_unificado'].value_counts().head(5).reset_index()
            top_cursos.columns = ['Curso', 'Quantidade']

            st.dataframe(
                top_cursos,
                hide_index=True,
                width="stretch"
            )
        else:
            st.info("Coluna 'curso_unificado' não disponível.")

    st.markdown("---")

    # ================================
    # 📋 TABELA FINAL
    # ================================
    st.subheader("📋 Tabela Completa de Dados")
    st.caption("Visualização de todos os TCCs conforme os filtros aplicados.")

    st.markdown(f"**Total exibido:** {len(df):,} registros".replace(",", "."))

    if "ano" in df.columns:
        df_ordenado = df.sort_values(by='ano', ascending=False)
    else:
        df_ordenado = df

    st.dataframe(
        df_ordenado,
        width="stretch",
        hide_index=True
    )