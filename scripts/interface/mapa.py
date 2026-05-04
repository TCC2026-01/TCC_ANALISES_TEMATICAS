# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import re


# ==============================
# 🔎 UF
# ==============================
def extrair_uf(row):
    if "uf" in row and pd.notna(row["uf"]):
        uf = str(row["uf"]).strip().upper()
        if len(uf) == 2:
            return uf

    if "instituicao" in row and pd.notna(row["instituicao"]):
        texto = str(row["instituicao"]).upper()

        match = re.search(r"\b([A-Z]{2})\b$", texto)
        if match:
            return match.group(1)

        mapa_if = {
            "IFMG": "MG", "IFSP": "SP", "IFRJ": "RJ", "IFRS": "RS",
            "IFSC": "SC", "IFBA": "BA", "IFGO": "GO", "IFTO": "TO",
            "IFMT": "MT", "IFPA": "PA", "IFAM": "AM", "IFCE": "CE",
            "IFPE": "PE", "IFRN": "RN", "IFPB": "PB", "IFAL": "AL",
            "IFS": "SE", "IFPI": "PI", "IFMA": "MA", "IFRO": "RO",
            "IFAC": "AC", "IFRR": "RR", "IFAP": "AP", "IFPR": "PR",
            "IFES": "ES", "IFG": "GO", "IFNMG": "MG", "IFSUL": "RS",
            "IFSULDEMINAS": "MG", "IFSUDESTE": "MG", "IFB": "DF",
        }

        for sigla, uf in mapa_if.items():
            if sigla in texto:
                return uf

    return None


# ==============================
# 🏷️ IF
# ==============================
def extrair_if(texto):
    if pd.isna(texto):
        return "OUTROS"

    texto = str(texto).upper()

    lista_if = [
        "IFMG","IFSP","IFRJ","IFRS","IFSC","IFBA","IFGO","IFTO",
        "IFMT","IFPA","IFAM","IFCE","IFPE","IFRN","IFPB","IFAL",
        "IFS","IFPI","IFMA","IFRO","IFAC","IFRR","IFAP","IFPR",
        "IFES","IFG","IFNMG","IFSUL","IFSULDEMINAS","IFSUDESTE","IFB"
    ]

    for i in lista_if:
        if i in texto:
            return i

    return "OUTROS"


# ==============================
# 🌎 DASHBOARD
# ==============================
def exibir(df_tcc, df_art, df_proj):

    st.subheader("🗺️ DISTRIBUIÇÃO GEOGRÁFICA DA PRODUÇÃO ACADÊMICA")

    # ==============================
    # UNIFICAR BASE
    # ==============================
    dfs = []

    if df_tcc is not None and not df_tcc.empty:
        tmp = df_tcc.copy()
        tmp["tipo"] = "TCC"
        dfs.append(tmp)

    if df_art is not None and not df_art.empty:
        tmp = df_art.copy()
        tmp["tipo"] = "ARTIGO CIENTÍFICO"
        dfs.append(tmp)

    if df_proj is not None and not df_proj.empty:
        tmp = df_proj.copy()
        tmp["tipo"] = "PROJETO"
        dfs.append(tmp)

    if not dfs:
        st.warning("NENHUM DADO DISPONÍVEL.")
        return

    df = pd.concat(dfs, ignore_index=True)

    # ==============================
    # UF + IF
    # ==============================
    df["UF"] = df.apply(extrair_uf, axis=1)
    df["INSTITUTO FEDERAL"] = df["instituicao"].apply(extrair_if)

    df = df[df["UF"].notna()]

    if df.empty:
        st.error("NÃO FOI POSSÍVEL IDENTIFICAR UFs.")
        return

    # ==============================
    # FILTRO
    # ==============================
    tipo_sel = st.multiselect(
        "TIPO DE PRODUÇÃO ACADÊMICA:",
        df["tipo"].unique().tolist(),
        default=df["tipo"].unique().tolist()
    )

    df = df[df["tipo"].isin(tipo_sel)]

    # ==============================
    # BASE MAPA
    # ==============================
    df_base = df.groupby("UF").size().reset_index(name="TOTAL DE REGISTROS")

    df_break = df.groupby(["UF", "tipo"]).size().unstack(fill_value=0).reset_index()

    df_if = df.groupby("UF")["INSTITUTO FEDERAL"].apply(
        lambda x: ", ".join(sorted(set(x)))
    ).reset_index()

    df_base = df_base.merge(df_break, on="UF", how="left").merge(df_if, on="UF", how="left")

    df_base = df_base.fillna(0)

    # ==============================
    # 🌎 MAPA
    # ==============================
    GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

    fig = px.choropleth(
        df_base,
        geojson=GEOJSON_URL,
        locations="UF",
        featureidkey="properties.sigla",
        color="TOTAL DE REGISTROS",
        color_continuous_scale="Blues",
        hover_data={
            "TOTAL DE REGISTROS": True,
            "TCC": True,
            "ARTIGO CIENTÍFICO": True,
            "PROJETO": True,
            "INSTITUTO FEDERAL": True
        },
        labels={
            "TOTAL DE REGISTROS": "TOTAL DE PRODUÇÕES",
            "TCC": "TRABALHOS DE CONCLUSÃO DE CURSO",
            "ARTIGO CIENTÍFICO": "ARTIGOS CIENTÍFICOS",
            "PROJETO": "PROJETOS ACADÊMICOS",
            "INSTITUTO FEDERAL": "INSTITUTOS FEDERAIS"
        }
    )

    fig.update_geos(fitbounds="locations", visible=False)

    fig.update_layout(
        height=550,
        margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_colorbar=dict(
            title="TOTAL DE PRODUÇÕES ACADÊMICAS"
        )
    )

    st.plotly_chart(fig, use_container_width=True)


    # ==============================
    # 📊 RANKING
    # ==============================
    st.markdown("### 📊 RANKING POR ESTADO")

    df_rank = df.groupby(["UF", "tipo"]).size().reset_index(name="QUANTIDADE")

    fig_rank = px.bar(
        df_rank.sort_values("QUANTIDADE", ascending=True),
        x="QUANTIDADE",
        y="UF",
        color="tipo",
        orientation="h",
        text="QUANTIDADE",
        color_discrete_map={
            "TCC": "#1f77b4",
            "ARTIGO CIENTÍFICO": "#2ca02c",
            "PROJETO": "#ff7f0e"
        },
        labels={
            "UF": "UNIDADE FEDERATIVA",
            "QUANTIDADE": "TOTAL DE REGISTROS",
            "tipo": "TIPO DE PRODUÇÃO"
        }
    )

    fig_rank.update_traces(textposition="outside")

    fig_rank.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="TIPO DE PRODUÇÃO ACADÊMICA"
    )

    st.plotly_chart(fig_rank, use_container_width=True)


    # ==============================
    # 📋 TABELA FINAL
    # ==============================
    st.markdown("### 📋 DISTRIBUIÇÃO DETALHADA POR UF, IF E TIPO")

    df_detalhe = (
        df.groupby(["UF", "INSTITUTO FEDERAL", "tipo"])
        .size()
        .reset_index(name="QUANTIDADE")
        .sort_values(["UF", "QUANTIDADE"], ascending=[True, False])
    )

    st.dataframe(df_detalhe, use_container_width=True, hide_index=True)