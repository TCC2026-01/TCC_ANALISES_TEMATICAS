# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px


# =============================
# 🧼 LIMPEZA
# =============================
def limpar_prefixo(texto):

    if not isinstance(texto, str):
        return texto

    return (
        texto
        .replace("TCC - ", "")
        .replace("Projeto - ", "")
        .replace("Artigo - ", "")
    )


# =============================
# 🧠 DASHBOARD
# =============================
def exibir(df_tcc, df_art, df_proj):

    st.subheader("📊 ANÁLISE DE TEMÁTICAS ACADÊMICAS")

    # =====================================================
    # 🔗 UNIFICAR BASES
    # =====================================================

    def preparar(df, tipo):

        if df is None or df.empty:
            return pd.DataFrame()

        tmp = df.copy()
        tmp["tipo"] = tipo

        return tmp

    df_tcc = preparar(df_tcc, "TCC")
    df_art = preparar(df_art, "Artigo")
    df_proj = preparar(df_proj, "Projeto")

    df = pd.concat(
        [df_tcc, df_art, df_proj],
        ignore_index=True
    )

    if df.empty:
        st.warning("Sem dados disponíveis.")
        return

    # =====================================================
    # 🎛️ FILTRO INTERNO
    # =====================================================

    st.markdown("## 🎛️ Filtros da Análise")

    tipos_disponiveis = (
        df["tipo"]
        .dropna()
        .unique()
        .tolist()
    )

    tipos_selecionados = st.multiselect(
        "Selecione os tipos de produção",
        options=sorted(tipos_disponiveis),
        default=sorted(tipos_disponiveis),
        key="filtro_tipo_storyline"
    )

    if not tipos_selecionados:
        st.warning("Selecione ao menos um tipo.")
        return

    # aplica filtro
    df = df[
        df["tipo"].isin(tipos_selecionados)
    ]

    st.markdown("---")

    # =====================================================
    # 📊 INSIGHT BASE
    # =====================================================

    total = len(df)

    top_geral = (
        df["nome_topico"]
        .value_counts()
        .head(1)
    )

    tema_top = (
        limpar_prefixo(top_geral.index[0])
        if not top_geral.empty
        else "N/A"
    )

    freq_top = (
        int(top_geral.values[0])
        if not top_geral.empty
        else 0
    )

    dominancia = (
        (freq_top / total) * 100
        if total > 0
        else 0
    )

    # =====================================================
    # 📖 STORYLINE
    # =====================================================

    st.markdown("## 📌 STORYLINE DAS TEMÁTICAS")

    st.info(f"""
Foram analisados **{total} registros acadêmicos**.

O tema mais recorrente foi **{tema_top}**, com **{freq_top} ocorrências**.
""")

    if dominancia > 30:

        st.warning(
            f"🔴 Forte concentração temática em "
            f"**{tema_top}** ({dominancia:.1f}%)."
        )

    elif dominancia > 15:

        st.info(
            f"🟡 Tema dominante moderado "
            f"(**{tema_top}**)."
        )

    else:

        st.success("🟢 Boa diversidade temática.")

    st.markdown("---")

    # =====================================================
    # 📊 MÉTRICAS COM TOOLTIP
    # =====================================================

    def top_tema(df_local, tipo):

        df_t = df_local[
            df_local["tipo"] == tipo
        ]

        if (
            df_t.empty
            or "nome_topico" not in df_t.columns
        ):
            return "N/A", 0

        top = (
            df_t["nome_topico"]
            .value_counts()
            .reset_index()
        )

        top.columns = [
            "tema",
            "qtd"
        ]

        return (
            limpar_prefixo(top.iloc[0]["tema"]),
            int(top.iloc[0]["qtd"])
        )

    col1, col2, col3 = st.columns(3)

    with col1:

        if "TCC" in tipos_selecionados:

            tema, qtd = top_tema(df, "TCC")

            st.metric(
                label="🎓 TOP TCC",
                value=tema,
                delta=f"{qtd} registros",
                help=f"""
Tema mais recorrente entre os TCCs.

Tema:
{tema}

Quantidade:
{qtd} registros
"""
            )

    with col2:

        if "Artigo" in tipos_selecionados:

            tema, qtd = top_tema(df, "Artigo")

            st.metric(
                label="📄 TOP ARTIGO",
                value=tema,
                delta=f"{qtd} registros",
                help=f"""
Tema mais recorrente entre os artigos.

Tema:
{tema}

Quantidade:
{qtd} registros
"""
            )

    with col3:

        if "Projeto" in tipos_selecionados:

            tema, qtd = top_tema(df, "Projeto")

            st.metric(
                label="🧪 TOP PROJETO",
                value=tema,
                delta=f"{qtd} registros",
                help=f"""
Tema mais recorrente entre os projetos.

Tema:
{tema}

Quantidade:
{qtd} registros
"""
            )

    st.markdown("---")

    # =====================================================
    # 📈 EVOLUÇÃO TEMPORAL
    # =====================================================

    if "ano" in df.columns:

        st.markdown(
            "## 📈 🧠 TEMAS DOMINANTES POR ANO"
        )

        df_time = (
            df.groupby(["ano", "tipo"])
            .size()
            .reset_index(name="qtd")
        )

        top_por_ano = (
            df.groupby("ano")["nome_topico"]
            .apply(
                lambda x:
                limpar_prefixo(
                    x.value_counts().index[0]
                )
            )
            .reset_index()
            .rename(
                columns={
                    "nome_topico":
                    "tema_dominante"
                }
            )
        )

        df_time = df_time.merge(
            top_por_ano,
            on="ano",
            how="left"
        )

        fig = px.line(
            df_time,
            x="ano",
            y="qtd",
            color="tipo",
            markers=True,
            title="🧠 TEMAS DOMINANTES POR ANO",
            labels={
                "ano": "ANO",
                "qtd": "QUANTIDADE",
                "tipo": "TIPO DE PRODUÇÃO"
            },
            hover_data={
                "tema_dominante": True,
                "qtd": True,
                "ano": True
            }
        )

        if not df_time.empty:

            max_row = df_time.loc[
                df_time["qtd"].idxmax()
            ]

            fig.add_annotation(
                x=max_row["ano"],
                y=max_row["qtd"],
                text="🔥 pico de produção",
                showarrow=True,
                arrowhead=2
            )

        fig.update_layout(
            height=500,
            title_x=0.5
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "ℹ️ Coluna 'ano' não encontrada — "
            "gráfico temporal não disponível."
        )

    st.markdown("---")

    # =====================================================
    # 📊 COMPARATIVO DE TEMAS
    # =====================================================

    st.markdown(
        "## 📊 TOP TEMÁTICAS (COMPARATIVO)"
    )

    def preparar_top(df_local, tipo):

        if (
            df_local.empty
            or "nome_topico"
            not in df_local.columns
        ):
            return pd.DataFrame(
                columns=[
                    "tema",
                    "qtd",
                    "tipo"
                ]
            )

        top = (
            df_local["nome_topico"]
            .value_counts()
            .head(10)
            .reset_index()
        )

        top.columns = [
            "tema",
            "qtd"
        ]

        top["tema"] = (
            top["tema"]
            .apply(limpar_prefixo)
        )

        top["tipo"] = tipo

        return top

    dfs = []

    for t in tipos_selecionados:

        dfs.append(
            preparar_top(
                df[df["tipo"] == t],
                t
            )
        )

    if dfs:

        df_chart = pd.concat(
            dfs,
            ignore_index=True
        )

        fig = px.bar(
            df_chart,
            x="tema",
            y="qtd",
            color="tipo",
            text="qtd",
            labels={
                "tema": "TEMA",
                "qtd": "QUANTIDADE",
                "tipo": "TIPO DE PRODUÇÃO"
            }
        )

        fig.update_traces(
            textposition="outside"
        )

        fig.update_layout(
            height=500,
            xaxis_title="TEMA",
            yaxis_title="QUANTIDADE",
            legend_title="TIPO DE PRODUÇÃO"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Selecione ao menos um tipo."
        )