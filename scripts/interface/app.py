# -*- coding: utf-8 -*-
import streamlit as st
from dados import carregar_dados
<<<<<<< HEAD
=======
import pandas as pd
>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
from utilitarios import filtrar_dados
from estilo import aplicar_estilo

# Módulos TCC (originais, sem alteração)
import visao_geral
import orientadores
import instituicoes
import tematicas
import busca_avancada
import tendencias

# Módulos Artigos
import artigos_visao_geral
import artigos_tematicas
import artigos_instituicoes
import artigos_busca
import artigos_tendencias

# Módulos Projetos
import projetos_visao_geral
import projetos_tematicas
import projetos_instituicoes
import projetos_busca
import projetos_tendencias

st.set_page_config(
    page_title="Panorama Temático de TCCs",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

aplicar_estilo()

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        margin-top: 0rem !important;
    }
<<<<<<< HEAD
=======

>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
    header[data-testid="stHeader"] {
        height: 0rem;
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ── NAVEGAÇÃO PRINCIPAL ───────────────────────────────────────────────────────
tipo_selecionado = st.segmented_control(
    label="Base de dados",
    options=["📊 Dados Gerais", "📚 TCCs", "🔬 Artigos", "🗂️ Projetos"],
    default="📊 Dados Gerais",
    label_visibility="collapsed"
)

PARQUET_MAP = {
    "📚 TCCs":     "tccs_dashboard.parquet",
    "🔬 Artigos":  "artigos_dashboard.parquet",
    "🗂️ Projetos": "projetos_dashboard.parquet",
}

with st.spinner("🚀 Carregando o projeto e preparando os dados..."):
<<<<<<< HEAD
=======

>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
    if tipo_selecionado == "📊 Dados Gerais":
        df_tcc = carregar_dados("tccs_dashboard.parquet")
        df = df_tcc
    else:
        df = carregar_dados(PARQUET_MAP[tipo_selecionado])

<<<<<<< HEAD
# Carrega artigos e projetos só quando Dados Gerais for selecionado e necessário
df_art  = None
df_proj = None
if tipo_selecionado == "📊 Dados Gerais":
    with st.spinner("⬇️ Carregando artigos..."):
        df_art = carregar_dados("artigos_dashboard.parquet")
=======
# ── DADOS GERAIS ──────────────────────────────────────────────────────────────
df_art = None
df_proj = None

if tipo_selecionado == "📊 Dados Gerais":

    with st.spinner("⬇️ Carregando artigos..."):
        df_art = carregar_dados("artigos_dashboard.parquet")

>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
    with st.spinner("⬇️ Carregando projetos..."):
        df_proj = carregar_dados("projetos_dashboard.parquet")

# ── BANNER ────────────────────────────────────────────────────────────────────
TITULOS = {
<<<<<<< HEAD
    "📊 Dados Gerais": ("Panorama da Produção Acadêmica na Rede Federal", "Análise Comparativa de TCCs, Artigos e Projetos"),
    "📚 TCCs":         ("Panorama Temático de TCCs na Rede Federal",      "Análise Inteligente de Trabalhos de Conclusão de Curso"),
    "🔬 Artigos":      ("Panorama de Artigos Científicos na Rede Federal", "Análise Inteligente de Artigos Científicos"),
    "🗂️ Projetos":     ("Panorama de Projetos Acadêmicos na Rede Federal", "Análise Inteligente de Projetos Acadêmicos"),
}

titulo, subtitulo = TITULOS[tipo_selecionado]
st.markdown(f"""
<div class="main-header">
    <h1>{titulo}</h1>
    <p style='margin: 5px 0 0 0; font-size: 1.1em;'>{subtitulo}</p>
</div>
""", unsafe_allow_html=True)

# ── FILTROS LATERAIS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")

    anos = None
    cursos = []
    tipos = []
    topicos = []
    inst = []

    if tipo_selecionado != "📊 Dados Gerais":
        inst = st.multiselect("Instituições", options=sorted(df['instituicao'].dropna().unique()))
        topicos = st.multiselect("Temas", options=sorted(df['nome_topico'].dropna().unique()))

        if tipo_selecionado != "🗂️ Projetos":
            ano_min = int(df['ano'].min())
            ano_max = int(df['ano'].max())
            anos = st.slider("Período", min_value=ano_min, max_value=ano_max, value=(ano_min, ano_max))

        if tipo_selecionado == "📚 TCCs":
            cursos = st.multiselect("Cursos", options=sorted(df['curso_unificado'].dropna().unique()))
            tipos = st.multiselect("Tipo de registro", options=sorted(df['tipo'].dropna().unique()), default=sorted(df['tipo'].dropna().unique()))

# ── FILTRAR ───────────────────────────────────────────────────────────────────
if tipo_selecionado == "📊 Dados Gerais":
    df_filtrado = df_tcc
else:
    df_filtrado = filtrar_dados(df, inst, anos if anos else (0, 9999), topicos, cursos, tipos)

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados. Ajuste os filtros na lateral.")
    st.stop()

# ── CSS ABAS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    button[data-baseweb="tab"] {
        font-weight: bold;
        padding: 10px 15px;
        margin-right: 10px;
        border-radius: 8px 8px 8px 8px;
        background-color: #F0F2F6;
        border-bottom: 2px solid transparent;
    }
</style>
""", unsafe_allow_html=True)

# ── ABAS POR TIPO ─────────────────────────────────────────────────────────────
if tipo_selecionado == "📚 TCCs":
    abas = st.tabs(["Visão Geral", "Orientadores", "Instituições", "Temáticas", "Busca Avançada", "Tendências"])
    with abas[0]: visao_geral.exibir(df_filtrado)
    with abas[1]: orientadores.exibir(df_filtrado)
    with abas[2]: instituicoes.exibir(df_filtrado)
    with abas[3]: tematicas.exibir(df_filtrado)
    with abas[4]: busca_avancada.exibir(df_filtrado)
    with abas[5]: tendencias.exibir(df_filtrado)

elif tipo_selecionado == "🔬 Artigos":
    import artigos_servidores
    abas = st.tabs(["Visão Geral", "Temáticas", "Instituições", "Servidores", "Busca", "Tendências"])
    with abas[0]: artigos_visao_geral.exibir(df_filtrado)
    with abas[1]: artigos_tematicas.exibir(df_filtrado)
    with abas[2]: artigos_instituicoes.exibir(df_filtrado)
    with abas[3]: artigos_servidores.exibir(df_filtrado)
    with abas[4]: artigos_busca.exibir(df_filtrado)
    with abas[5]: artigos_tendencias.exibir(df_filtrado)

elif tipo_selecionado == "🗂️ Projetos":
    import projetos_servidores
    abas = st.tabs(["Visão Geral", "Temáticas", "Instituições", "Servidores", "Busca", "Tendências"])
    with abas[0]: projetos_visao_geral.exibir(df_filtrado)
    with abas[1]: projetos_tematicas.exibir(df_filtrado)
    with abas[2]: projetos_instituicoes.exibir(df_filtrado)
    with abas[3]: projetos_servidores.exibir(df_filtrado)
    with abas[4]: projetos_busca.exibir(df_filtrado)
    with abas[5]: projetos_tendencias.exibir(df_filtrado)

elif tipo_selecionado == "📊 Dados Gerais":
    abas_dg = st.tabs(["Visão Geral", "Temáticas", "Servidores", "Mapa"])
    with abas_dg[0]:
        import comparacoes
        comparacoes.exibir(df_tcc, df_art, df_proj)
    with abas_dg[1]:
        import dados_gerais_tematicas
        dados_gerais_tematicas.exibir(df_tcc, df_art, df_proj)
    with abas_dg[2]:
        import dados_gerais_servidores
        dados_gerais_servidores.exibir(df_tcc, df_art, df_proj)
=======
    "📊 Dados Gerais": (
        "Panorama da Produção Acadêmica na Rede Federal",
        "Análise Comparativa de TCCs, Artigos e Projetos"
    ),

    "📚 TCCs": (
        "Panorama Temático de TCCs na Rede Federal",
        "Análise Inteligente de Trabalhos de Conclusão de Curso"
    ),

    "🔬 Artigos": (
        "Panorama de Artigos Científicos na Rede Federal",
        "Análise Inteligente de Artigos Científicos"
    ),

    "🗂️ Projetos": (
        "Panorama de Projetos Acadêmicos na Rede Federal",
        "Análise Inteligente de Projetos Acadêmicos"
    ),
}

titulo, subtitulo = TITULOS[tipo_selecionado]

st.markdown(f"""
<div class="main-header">
    <h1>{titulo}</h1>
    <p style='margin: 5px 0 0 0; font-size: 1.1em;'>
        {subtitulo}
    </p>
</div>
""", unsafe_allow_html=True)

# ── FILTROS LATERAIS ──────────────────────────────────────────────────────────
with st.sidebar:

    st.header("Filtros")

    anos = None
    cursos = []
    tipos = []
    topicos = []
    inst = []

    # ──────────────────────────────────────────────────────────────────────────
    # DADOS GERAIS
    # ──────────────────────────────────────────────────────────────────────────
    if tipo_selecionado == "📊 Dados Gerais":

        base_inst = sorted(
            set(df_tcc['instituicao'].dropna().unique()) |
            set(df_art['instituicao'].dropna().unique()) |
            set(df_proj['instituicao'].dropna().unique())
        )

        base_top = sorted(
            set(df_tcc['nome_topico'].dropna().unique()) |
            set(df_art['nome_topico'].dropna().unique()) |
            set(df_proj['nome_topico'].dropna().unique())
        )

        inst = st.multiselect("Instituições", base_inst
        )

        topicos = st.multiselect("Temas", base_top
        )

        anos_validos = [
            int(v)
            for v in pd.concat(
                [df_tcc['ano'], df_art['ano']],
                ignore_index=True
            ).dropna().astype(int).tolist()
        ]

        if anos_validos:

            anos = st.slider(
                "Período",
                min_value=min(anos_validos),
                max_value=max(anos_validos),
                value=(min(anos_validos), max(anos_validos))
            )

    # ──────────────────────────────────────────────────────────────────────────
    # DEMAIS ABAS
    # ──────────────────────────────────────────────────────────────────────────
    else:

        inst = st.multiselect("Instituições", sorted(df['instituicao'].dropna().unique())
        )

        topicos = st.multiselect("Temas", sorted(df['nome_topico'].dropna().unique())
        )

        if tipo_selecionado != "🗂️ Projetos":

            ano_min = int(df['ano'].min())
            ano_max = int(df['ano'].max())

            anos = st.slider(
                "Período",
                min_value=ano_min,
                max_value=ano_max,
                value=(ano_min, ano_max)
            )

        # ──────────────────────────────────────────────────────────────────────
        # TCCs
        # ──────────────────────────────────────────────────────────────────────
        if tipo_selecionado == "📚 TCCs":

            cursos = st.multiselect("Cursos", sorted(
                    df['curso_unificado'].dropna().unique()
                )
            )

            # ==============================================================
            # FILTRO FIXO INVISÍVEL
            # ==============================================================
            # A aba já é exclusivamente TCC.
            # Mantemos os tipos para preservar compatibilidade interna,
            # mas removemos o multiselect visual.
            # ==============================================================

            tipos = sorted(df['tipo'].dropna().unique())

# ── FILTRAR ───────────────────────────────────────────────────────────────────
if tipo_selecionado == "📊 Dados Gerais":

    df_tcc = filtrar_dados(
        df_tcc,
        inst,
        anos if anos else (0, 9999),
        topicos
    )

    df_art = filtrar_dados(
        df_art,
        inst,
        anos if anos else (0, 9999),
        topicos
    )

    df_proj = filtrar_dados(
        df_proj,
        inst,
        None,
        topicos
    )

    df_filtrado = df_tcc

else:

    df_filtrado = filtrar_dados(
        df,
        inst,
        anos if anos else (0, 9999),
        topicos,
        cursos,
        tipos
    )

# ── VALIDAÇÃO ─────────────────────────────────────────────────────────────────
if df_filtrado.empty:

    st.warning(
        "Nenhum dado encontrado para os filtros selecionados. "
        "Ajuste os filtros na lateral."
    )

    st.stop()

# ── CSS ABAS ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>

button[data-baseweb="tab"] {
    font-weight: bold;
    padding: 10px 15px;
    margin-right: 10px;
    border-radius: 8px;
    background-color: #F0F2F6;
    border-bottom: 2px solid transparent;
}

</style>
""", unsafe_allow_html=True)

# ── ABAS POR TIPO ─────────────────────────────────────────────────────────────
if tipo_selecionado == "📚 TCCs":

    abas = st.tabs([
        "Visão Geral",
        "Orientadores",
        "Instituições",
        "Temáticas",
        "Busca Avançada",
        "Tendências"
    ])

    with abas[0]:
        visao_geral.exibir(df_filtrado)

    with abas[1]:
        orientadores.exibir(df_filtrado)

    with abas[2]:
        instituicoes.exibir(df_filtrado)

    with abas[3]:
        tematicas.exibir(df_filtrado)

    with abas[4]:
        busca_avancada.exibir(df_filtrado)

    with abas[5]:
        tendencias.exibir(df_filtrado)

elif tipo_selecionado == "🔬 Artigos":

    import artigos_servidores

    abas = st.tabs([
        "Visão Geral",
        "Temáticas",
        "Instituições",
        "Servidores",
        "Busca",
        "Tendências"
    ])

    with abas[0]:
        artigos_visao_geral.exibir(df_filtrado)

    with abas[1]:
        artigos_tematicas.exibir(df_filtrado)

    with abas[2]:
        artigos_instituicoes.exibir(df_filtrado)

    with abas[3]:
        artigos_servidores.exibir(df_filtrado)

    with abas[4]:
        artigos_busca.exibir(df_filtrado)

    with abas[5]:
        artigos_tendencias.exibir(df_filtrado)

elif tipo_selecionado == "🗂️ Projetos":

    import projetos_servidores

    abas = st.tabs([
        "Visão Geral",
        "Temáticas",
        "Instituições",
        "Servidores",
        "Busca",
        "Tendências"
    ])

    with abas[0]:
        projetos_visao_geral.exibir(df_filtrado)

    with abas[1]:
        projetos_tematicas.exibir(df_filtrado)

    with abas[2]:
        projetos_instituicoes.exibir(df_filtrado)

    with abas[3]:
        projetos_servidores.exibir(df_filtrado)

    with abas[4]:
        projetos_busca.exibir(df_filtrado)

    with abas[5]:
        projetos_tendencias.exibir(df_filtrado)

elif tipo_selecionado == "📊 Dados Gerais":

    abas_dg = st.tabs([
        "Visão Geral",
        "Temáticas",
        "Servidores",
        "Mapa"
    ])

    with abas_dg[0]:
        import comparacoes
        comparacoes.exibir(df_tcc, df_art, df_proj)

    with abas_dg[1]:
        import dados_gerais_tematicas
        dados_gerais_tematicas.exibir(df_tcc, df_art, df_proj)

    with abas_dg[2]:
        import dados_gerais_servidores
        dados_gerais_servidores.exibir(df_tcc, df_art, df_proj)

>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
    with abas_dg[3]:
        import mapa
        mapa.exibir(df_tcc, df_art, df_proj)

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown("---")
<<<<<<< HEAD
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Dashboard de Trabalhos de Conclusão de Curso da Rede Federal</strong></p>
    <p>Desenvolvido por Ana Luísa Caixeta, Anna Caroline Ribeiro, Felipe Gomes e Geovana Perazzo - 2025</p>
=======

st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>

<p>
<strong>
Dashboard de Trabalhos de Conclusão de Curso da Rede Federal
</strong>
</p>

<p>
Desenvolvido por Ana Luísa Caixeta, Anna Caroline Ribeiro,
Felipe Gomes e Geovana Perazzo - 2025
</p>

>>>>>>> c3eb28a (ultima atualização do pre-process e da insterface)
</div>
""", unsafe_allow_html=True)