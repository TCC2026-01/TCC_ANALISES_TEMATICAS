# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import pandas as pd
from utilitarios import metric_bold

def exibir(df_tcc, df_art, df_proj):
    st.subheader("Comparação entre Servidores")
    st.caption("Selecione uma instituição e os servidores que deseja comparar")

    cores = ['#2C5F8A', '#1A7A5E', '#B85C00', '#7B2D8B', '#8B1A1A']

    # ── FILTRO DE INSTITUIÇÃO ─────────────────────────────────────────────────
    todas_inst = sorted(set(
        df_tcc['instituicao'].dropna().unique().tolist() +
        df_art['instituicao'].dropna().unique().tolist() +
        df_proj['instituicao'].dropna().unique().tolist()
    ))
    inst_sel = st.selectbox("Selecione uma Instituição", options=["Todas"] + todas_inst)

    if inst_sel != "Todas":
        df_tcc_f  = df_tcc[df_tcc['instituicao'] == inst_sel]
        df_art_f  = df_art[df_art['instituicao'] == inst_sel]
        df_proj_f = df_proj[df_proj['instituicao'] == inst_sel]
    else:
        df_tcc_f, df_art_f, df_proj_f = df_tcc, df_art, df_proj

    # ── LISTA DE SERVIDORES ───────────────────────────────────────────────────
    servidores_tcc  = set(df_tcc_f['orientador'].dropna().unique().tolist())
    servidores_art  = set(df_art_f['autores'].dropna().unique().tolist())
    servidores_proj = set(df_proj_f['autores'].dropna().unique().tolist())
    todos_servidores = sorted(servidores_tcc | servidores_art | servidores_proj)

    servidores_sel = st.multiselect("Selecione os servidores para comparar (2 ou mais)", todos_servidores
    )

    if len(servidores_sel) < 2:
        st.info("Selecione pelo menos 2 servidores para comparar.")
        st.markdown("---")

        st.subheader("Top 5 Servidores por Categoria")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📚 Mais TCCs Orientados**")
            top_orient = df_tcc_f['orientador'].dropna().value_counts().head(5).reset_index()
            top_orient.columns = ['Servidor', 'TCCs']
            fig1 = px.bar(top_orient, x='TCCs', y='Servidor', orientation='h',
                          color_discrete_sequence=['#2C5F8A'], text='TCCs')
            fig1.update_traces(textposition='outside')
            fig1.update_layout(height=350, showlegend=False,
                               yaxis={'categoryorder': 'total ascending'},
                               xaxis_title="", margin=dict(l=180, r=60))
            st.plotly_chart(fig1, config={'responsive': True}, key="srv_top_tcc", use_container_width=True)

        with col2:
            st.markdown("**🔬 Mais Artigos Publicados**")
            top_art = df_art_f['autores'].dropna().value_counts().head(5).reset_index()
            top_art.columns = ['Servidor', 'Artigos']
            fig2 = px.bar(top_art, x='Artigos', y='Servidor', orientation='h',
                          color_discrete_sequence=['#1A7A5E'], text='Artigos')
            fig2.update_traces(textposition='outside')
            fig2.update_layout(height=350, showlegend=False,
                               yaxis={'categoryorder': 'total ascending'},
                               xaxis_title="", margin=dict(l=180, r=60))
            st.plotly_chart(fig2, config={'responsive': True}, key="srv_top_art", use_container_width=True)

        st.markdown("---")
        st.markdown("**🗂️ Top 5 por Natureza de Projeto**")

        naturezas = ['PESQUISA', 'EXTENSAO', 'ENSINO', 'DESENVOLVIMENTO', 'OUTRA']
        labels_nat = {
            'PESQUISA': 'Pesquisa',
            'EXTENSAO': 'Extensão',
            'ENSINO': 'Ensino',
            'DESENVOLVIMENTO': 'Desenvolvimento',
            'OUTRA': 'Outra'
        }
        cores_nat = ['#2C5F8A', '#1A7A5E', '#B85C00', '#7B2D8B', '#8B1A1A']

        cols_nat = st.columns(3)
        col_idx = 0
        for idx, nat in enumerate(naturezas):
            df_nat = df_proj_f[df_proj_f['natureza'] == nat]
            if df_nat.empty:
                continue
            top_nat = df_nat['autores'].dropna().value_counts().head(5).reset_index()
            top_nat.columns = ['Servidor', 'Projetos']
            with cols_nat[col_idx % 3]:
                st.markdown(f"**{labels_nat[nat]}**")
                fig_n = px.bar(top_nat, x='Projetos', y='Servidor', orientation='h',
                               color_discrete_sequence=[cores_nat[idx]], text='Projetos')
                fig_n.update_traces(textposition='outside')
                fig_n.update_layout(height=300, showlegend=False,
                                    yaxis={'categoryorder': 'total ascending'},
                                    xaxis_title="", margin=dict(l=160, r=50))
                st.plotly_chart(fig_n, config={'responsive': True},
                                key=f"srv_top_nat_{nat}", use_container_width=True)
            col_idx += 1
        return

    # ── FUNÇÃO DE DADOS ───────────────────────────────────────────────────────
    def dados_servidor(nome):
        tccs       = len(df_tcc_f[df_tcc_f['orientador'] == nome])
        artigos    = len(df_art_f[df_art_f['autores'] == nome])
        proj_total = len(df_proj_f[df_proj_f['autores'] == nome])
        proj_pesq  = len(df_proj_f[(df_proj_f['autores'] == nome) & (df_proj_f['natureza'] == 'PESQUISA')])
        proj_ext   = len(df_proj_f[(df_proj_f['autores'] == nome) & (df_proj_f['natureza'] == 'EXTENSAO')])
        proj_ens   = len(df_proj_f[(df_proj_f['autores'] == nome) & (df_proj_f['natureza'] == 'ENSINO')])
        proj_des   = len(df_proj_f[(df_proj_f['autores'] == nome) & (df_proj_f['natureza'] == 'DESENVOLVIMENTO')])

        inst = "—"
        for df_b, col in [(df_tcc_f, 'orientador'), (df_art_f, 'autores'), (df_proj_f, 'autores')]:
            s = df_b[df_b[col] == nome]['instituicao'].dropna()
            if not s.empty:
                inst = s.mode().iloc[0]
                break

        return {
            'TCCs Orientados': tccs,
            'Artigos Publicados': artigos,
            'Total de Projetos': proj_total,
            'Projetos Pesquisa': proj_pesq,
            'Projetos Extensão': proj_ext,
            'Projetos Ensino': proj_ens,
            'Projetos Desenvolvimento': proj_des,
            'Instituição': str(inst),
        }

    dados = {srv: dados_servidor(srv) for srv in servidores_sel}

    # ── CARDS DE PERFIL ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Perfil dos Servidores")
    cols_perfil = st.columns(len(servidores_sel))
    for i, srv in enumerate(servidores_sel):
        d = dados[srv]
        cor = cores[i % len(cores)]
        with cols_perfil[i]:
            st.markdown(f"""
            <div style='
                border: 1px solid #e0e0e0;
                border-top: 4px solid {cor};
                border-radius: 8px;
                padding: 20px;
                background: #ffffff;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            '>
                <p style='font-size:1.05em; font-weight:700; color:#1a1a1a; margin:0 0 4px 0;'>{srv}</p>
                <p style='font-size:0.85em; color:#666; margin:0 0 16px 0;'>🏫 {d['Instituição']}</p>
                <hr style='border:none; border-top:1px solid #eee; margin:12px 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <div style='text-align:center;'>
                        <p style='font-size:1.6em; font-weight:700; color:{cor}; margin:0;'>{d['TCCs Orientados']}</p>
                        <p style='font-size:0.75em; color:#888; margin:2px 0 0 0;'>TCCs</p>
                    </div>
                    <div style='text-align:center;'>
                        <p style='font-size:1.6em; font-weight:700; color:{cor}; margin:0;'>{d['Artigos Publicados']}</p>
                        <p style='font-size:0.75em; color:#888; margin:2px 0 0 0;'>Artigos</p>
                    </div>
                    <div style='text-align:center;'>
                        <p style='font-size:1.6em; font-weight:700; color:{cor}; margin:0;'>{d['Total de Projetos']}</p>
                        <p style='font-size:0.75em; color:#888; margin:2px 0 0 0;'>Projetos</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── COMPARAÇÃO VISUAL ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Comparação Visual")

    metricas_grupos = {
        "Produção Acadêmica": ['TCCs Orientados', 'Artigos Publicados'],
        "Projetos": ['Total de Projetos', 'Projetos Pesquisa', 'Projetos Extensão',
                     'Projetos Ensino', 'Projetos Desenvolvimento'],
    }

    for grupo, metricas_grupo in metricas_grupos.items():
        st.markdown(f"##### {grupo}")
        for metrica in metricas_grupo:
            valores = {srv: dados[srv][metrica] for srv in servidores_sel}
            max_val = max(valores.values()) if max(valores.values()) > 0 else 1
            st.markdown(f"<p style='font-size:0.9em; color:#444; margin:8px 0 4px 0;'><strong>{metrica}</strong></p>",
                        unsafe_allow_html=True)
            for j, srv in enumerate(servidores_sel):
                val = valores[srv]
                pct = int((val / max_val) * 100)
                cor = cores[j % len(cores)]
                nome_curto = " ".join([srv.split()[0], srv.split()[-1]]) if len(srv.split()) > 1 else srv
                badge = " ★" if val == max_val and max_val > 0 else ""
                st.markdown(f"""
                <div style='display:flex; align-items:center; margin-bottom:5px;'>
                    <div style='width:150px; font-size:0.82em; color:#333; text-align:right;
                                padding-right:12px; white-space:nowrap; overflow:hidden;
                                text-overflow:ellipsis;'>{nome_curto}{badge}</div>
                    <div style='flex:1; background:#f4f4f4; border-radius:3px; height:24px;'>
                        <div style='width:{max(pct,2)}%; background:{cor}; border-radius:3px;
                                    height:24px; display:flex; align-items:center;
                                    justify-content:flex-end; padding-right:8px;'>
                            <span style='color:white; font-weight:600; font-size:0.82em;'>{val}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    # ── TABELA RESUMO ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Resumo Comparativo")

    metricas = ['TCCs Orientados', 'Artigos Publicados', 'Total de Projetos',
                'Projetos Pesquisa', 'Projetos Extensão', 'Projetos Ensino', 'Projetos Desenvolvimento']

    rows = []
    for metrica in metricas:
        row = {'Métrica': metrica}
        valores = {srv: dados[srv][metrica] for srv in servidores_sel}
        max_val = max(valores.values()) if valores else 0
        for srv in servidores_sel:
            nome_curto = " ".join([srv.split()[0], srv.split()[-1]]) if len(srv.split()) > 1 else srv
            val = valores[srv]
            row[nome_curto] = f"★ {val}" if val == max_val and max_val > 0 else str(val)
        rows.append(row)

    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ── RANKING GERAL ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Ranking Geral")
    pontos = {srv: 0 for srv in servidores_sel}
    for metrica in metricas:
        valores = {srv: dados[srv][metrica] for srv in servidores_sel}
        max_val = max(valores.values()) if valores else 0
        if max_val > 0:
            for srv in servidores_sel:
                if valores[srv] == max_val:
                    pontos[srv] += 1

    df_pontos = pd.DataFrame({
        'Servidor': list(pontos.keys()),
        'Categorias Vencidas': list(pontos.values())
    }).sort_values('Categorias Vencidas', ascending=False)

    fig_rank = px.bar(df_pontos, x='Categorias Vencidas', y='Servidor', orientation='h',
                      color='Servidor', color_discrete_sequence=cores[:len(servidores_sel)],
                      text='Categorias Vencidas')
    fig_rank.update_traces(textposition='outside')
    fig_rank.update_layout(height=300, showlegend=False,
                           yaxis={'categoryorder': 'total ascending'},
                           xaxis_title="Categorias Vencidas",
                           plot_bgcolor='white', paper_bgcolor='white')
    st.plotly_chart(fig_rank, config={'responsive': True}, key="srv_rank", use_container_width=True)

    vencedor = df_pontos.iloc[0]['Servidor']
    pts = df_pontos.iloc[0]['Categorias Vencidas']
    st.info(f"**{vencedor}** lidera com **{pts}** categorias vencidas de {len(metricas)} analisadas.")