# -*- coding: utf-8 -*-
"""
Script ETL para Extrair, Transformar e Carregar dados para o Star Schema.

Atualizações:
- mantém o processamento dimensional de TCCs
- inclui `data_inicio` e `data_fim` em projetos
- mantém artigos e projetos como fatos auxiliares
"""

import sqlite3
import pandas as pd
import time
from sqlalchemy import create_engine
import unicodedata
from config import carregar_instituicoes
import os

RAW_DB_NAME = "integra.db"
PROCESSED_DB_NAME = "datamart.db"
PROCESSED_DB_ENGINE = f"sqlite:///{PROCESSED_DB_NAME}"
LOG_REJEITADOS_FILE = "log_tccs_rejeitados.csv"

print("Carregando dicionário de instituições...")
INSTITUICOES = carregar_instituicoes()


def normalize_string(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = text.replace("instituicao", "instituto")
    text = text.replace("institituto", "instituto")
    text = text.replace("instituo", "instituto")
    return text


def init_cap(series):
    return series.astype(str).str.title().str.strip()


def extrair_autores_orientador(autores_str):
    if not isinstance(autores_str, str):
        return [], None
    alunos, orientador = [], None
    partes = [p.strip() for p in autores_str.split(",")]
    for parte in partes:
        if "(Orientador/a)" in parte:
            orientador = parte.replace("(Orientador/a)", "").strip()
        else:
            alunos.append(parte)
    return alunos, orientador


def validar_tcc_rede_federal(row):
    sigla_alvo = row["sigla_alvo_coleta"]
    nome_bruto_tcc = row["nome_tcc_bruto"]

    if pd.isna(sigla_alvo) or pd.isna(nome_bruto_tcc):
        return None

    norm_text = normalize_string(nome_bruto_tcc)
    norm_sigla = normalize_string(sigla_alvo)

    is_general_federal = "instituto federal" in norm_text
    is_specific_sigla = norm_sigla in norm_text

    if is_general_federal or is_specific_sigla:
        return sigla_alvo
    return None


def logar_rejeitados(df_rejeitados, motivo_rejeicao, arquivo_log, modo="w"):
    if df_rejeitados.empty:
        return

    print(f"     - AVISO: {len(df_rejeitados)} registros serão descartados por '{motivo_rejeicao}'.")
    print(f"     - Logando rejeitados em '{arquivo_log}'...")

    df_log = df_rejeitados.copy()
    df_log["motivo_rejeicao"] = motivo_rejeicao

    escrever_cabecalho = (modo == "w") or (not os.path.exists(arquivo_log))
    df_log.to_csv(arquivo_log, mode=modo, index=False, header=escrever_cabecalho, encoding="utf-8-sig")


def main():
    start_time = time.time()
    print("Iniciando processo ETL para o Star Schema")

    if os.path.exists(LOG_REJEITADOS_FILE):
        os.remove(LOG_REJEITADOS_FILE)

    map_nomes_completos = {sigla: valores[0] for sigla, valores in INSTITUICOES.items()}

    print(f"\n1. Extraindo dados de '{RAW_DB_NAME}'...")
    try:
        with sqlite3.connect(RAW_DB_NAME) as conn:
            query = "SELECT *, instituicao as nome_tcc_bruto, sigla as sigla_alvo_coleta FROM tccs"
            df_raw = pd.read_sql_query(query, conn)

            try:
                df_artigos_raw = pd.read_sql_query("SELECT * FROM artigos", conn)
            except Exception:
                df_artigos_raw = pd.DataFrame()

            try:
                df_projetos_raw = pd.read_sql_query("SELECT * FROM projetos", conn)
            except Exception:
                df_projetos_raw = pd.DataFrame()

        print(f"   - Total de registros brutos extraídos: {len(df_raw)} TCCs")
        if not df_artigos_raw.empty:
            print(f"   - Total de registros brutos extraídos: {len(df_artigos_raw)} artigos")
        if not df_projetos_raw.empty:
            print(f"   - Total de registros brutos extraídos: {len(df_projetos_raw)} projetos")
    except Exception as e:
        print(f"   - ERRO: Falha ao ler o banco de dados bruto '{RAW_DB_NAME}'.")
        print(f"   - Detalhe: {e}")
        return

    print("\n2. Transformando dados...")
    df = df_raw.copy()
    print(f"   - Registros para processar (sem filtro de nível): {len(df)}")

    print("\n   - Criando Dimensão Instituição...")
    df_instituicao = pd.DataFrame.from_dict(INSTITUICOES, orient="index", columns=["nome_completo", "url", "uf"])
    df_instituicao["sigla"] = df_instituicao.index
    df_instituicao["nome_completo"] = df_instituicao["sigla"].map(map_nomes_completos)
    df_instituicao.reset_index(drop=True, inplace=True)
    df_instituicao["instituicao_id"] = df_instituicao.index + 1
    dim_instituicao = df_instituicao[["instituicao_id", "sigla", "nome_completo", "uf", "url"]]

    print("   - Validando TCCs da Rede Federal...")
    df["sigla_mapeada"] = df.apply(validar_tcc_rede_federal, axis=1)

    df_rejeitados_inst = df[df["sigla_mapeada"].isna()]
    logar_rejeitados(
        df_rejeitados_inst,
        "Instituição do TCC não parece ser da Rede Federal (ex: Universidade)",
        LOG_REJEITADOS_FILE,
        modo="w"
    )

    df.dropna(subset=["sigla_mapeada"], inplace=True)
    if len(df) == 0:
        print("   - Nenhum registro validado. Encerrando.")
        return

    df["lista_alunos"] = df["autores"].apply(extrair_autores_orientador).apply(lambda x: x[0])
    df["orientador"] = df["autores"].apply(extrair_autores_orientador).apply(lambda x: x[1])

    print("   - Criando Dimensões Campus, Curso e Pessoa...")
    dim_campus = pd.DataFrame(df["campus"].dropna().unique(), columns=["nome_campus"])
    dim_campus["nome_campus"] = init_cap(dim_campus["nome_campus"])
    dim_campus.sort_values("nome_campus", inplace=True)
    dim_campus["campus_id"] = range(1, len(dim_campus) + 1)

    dim_curso = pd.DataFrame(df["curso"].dropna().unique(), columns=["nome_curso"])
    dim_curso["nome_curso"] = init_cap(dim_curso["nome_curso"])
    dim_curso["nivel"] = "N/A"
    dim_curso.sort_values("nome_curso", inplace=True)
    dim_curso["curso_id"] = range(1, len(dim_curso) + 1)

    pessoas_unicas = pd.concat([df["lista_alunos"].explode(), df["orientador"]]).dropna().unique()
    dim_pessoa = pd.DataFrame(pessoas_unicas, columns=["nome_pessoa"])
    dim_pessoa["nome_pessoa"] = init_cap(dim_pessoa["nome_pessoa"])
    dim_pessoa.sort_values("nome_pessoa", inplace=True)
    dim_pessoa["pessoa_id"] = range(1, len(dim_pessoa) + 1)

    print("\n   - Criando Tabela Fato e Pontes...")
    df["tcc_id"] = range(1, len(df) + 1)

    map_instituicao = pd.Series(dim_instituicao.instituicao_id.values, index=dim_instituicao.sigla).to_dict()
    map_campus = pd.Series(dim_campus.campus_id.values, index=dim_campus.nome_campus).to_dict()
    map_curso = pd.Series(dim_curso.curso_id.values, index=dim_curso.nome_curso).to_dict()
    map_pessoa = pd.Series(dim_pessoa.pessoa_id.values, index=dim_pessoa.nome_pessoa).to_dict()

    df["instituicao_id"] = df["sigla_mapeada"].map(map_instituicao)
    df["campus_id"] = init_cap(df["campus"]).map(map_campus)
    df["curso_id"] = init_cap(df["curso"]).map(map_curso)

    colunas_fk = ["instituicao_id", "campus_id", "curso_id"]
    df_rejeitados_fk = df[df[colunas_fk].isna().any(axis=1)]
    logar_rejeitados(
        df_rejeitados_fk,
        "Falha ao mapear FK (Campus ou Curso nulo/inválido)",
        LOG_REJEITADOS_FILE,
        modo="a"
    )

    df.dropna(subset=colunas_fk, inplace=True)
    print(f"     - Registros restantes após garantir mapeamento FK: {len(df)}")

    fato_tcc = df[[
        "tcc_id", "titulo", "resumo", "palavras_chaves", "ano",
        "curso_id", "instituicao_id", "campus_id"
    ]]

    fato_artigo = None
    if not df_artigos_raw.empty:
        print("   - Transformando dados de artigos científicos...")
        df_art = df_artigos_raw.copy()
        df_art["titulo"] = df_art["titulo"].astype(str).str.strip()
        df_art["journal"] = df_art.get("journal", pd.Series([""] * len(df_art))).astype(str).str.strip()
        df_art["doi"] = df_art.get("doi", pd.Series([""] * len(df_art))).astype(str).str.strip()
        df_art["ano"] = df_art["ano"].astype(str).str.strip()
        df_art["palavras_chaves"] = df_art.get("palavras_chaves", pd.Series([""] * len(df_art))).astype(str).str.strip()
        df_art["resumo"] = df_art.get("resumo", pd.Series([""] * len(df_art))).astype(str).str.strip()
        df_art["artigo_id"] = range(1, len(df_art) + 1)
        fato_artigo = df_art[[
            "artigo_id", "slug_professor", "nome_professor", "sigla", "ano",
            "titulo", "journal", "doi", "palavras_chaves", "resumo"
        ]]

    fato_projeto = None
    if not df_projetos_raw.empty:
        print("   - Transformando dados de projetos...")
        df_proj = df_projetos_raw.copy()
        df_proj["titulo"] = df_proj["titulo"].astype(str).str.strip()
        df_proj["descricao"] = df_proj.get("descricao", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["natureza"] = df_proj.get("natureza", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["equipe"] = df_proj.get("equipe", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["financiadores"] = df_proj.get("financiadores", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["data_inicio"] = df_proj.get("data_inicio", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["data_fim"] = df_proj.get("data_fim", pd.Series([""] * len(df_proj))).astype(str).str.strip()
        df_proj["projeto_id"] = range(1, len(df_proj) + 1)
        fato_projeto = df_proj[[
            "projeto_id", "slug_professor", "nome_professor", "sigla",
            "titulo", "descricao", "natureza", "equipe", "financiadores",
            "data_inicio", "data_fim"
        ]]

    ponte_tcc_aluno = df[["tcc_id", "lista_alunos"]].explode("lista_alunos").rename(columns={"lista_alunos": "nome_pessoa"})
    ponte_tcc_aluno["aluno_id"] = init_cap(ponte_tcc_aluno["nome_pessoa"]).map(map_pessoa)
    ponte_tcc_aluno = ponte_tcc_aluno[["tcc_id", "aluno_id"]].dropna()

    ponte_tcc_orientador = df[["tcc_id", "orientador"]].rename(columns={"orientador": "nome_pessoa"})
    ponte_tcc_orientador["orientador_id"] = init_cap(ponte_tcc_orientador["nome_pessoa"]).map(map_pessoa)
    ponte_tcc_orientador = ponte_tcc_orientador[["tcc_id", "orientador_id"]].dropna()

    print(f"\n3. Carregando dados no Data Mart '{PROCESSED_DB_NAME}'...")
    engine = create_engine(PROCESSED_DB_ENGINE)

    try:
        dim_instituicao.to_sql("dim_instituicao", engine, if_exists="replace", index=False)
        dim_campus.to_sql("dim_campus", engine, if_exists="replace", index=False)
        dim_curso.to_sql("dim_curso", engine, if_exists="replace", index=False)
        dim_pessoa.to_sql("dim_pessoa", engine, if_exists="replace", index=False)
        fato_tcc.to_sql("fato_tcc", engine, if_exists="replace", index=False)
        ponte_tcc_aluno.to_sql("ponte_tcc_aluno", engine, if_exists="replace", index=False)
        ponte_tcc_orientador.to_sql("ponte_tcc_orientador", engine, if_exists="replace", index=False)

        if fato_artigo is not None:
            fato_artigo.to_sql("fato_artigo", engine, if_exists="replace", index=False)
            print(f"   - Carga de {len(fato_artigo)} artigos científicos concluída.")

        if fato_projeto is not None:
            fato_projeto.to_sql("fato_projeto", engine, if_exists="replace", index=False)
            print(f"   - Carga de {len(fato_projeto)} projetos concluída.")

        print("   - Carga de dados concluída.")

    except Exception as e:
        print(f"   - ERRO: Falha ao carregar dados no Data Mart.")
        print(f"   - Detalhe: {e}")
        return

    end_time = time.time()
    print(f"\n--- Processo ETL finalizado em {end_time - start_time:.2f} segundos. ---")


if __name__ == "__main__":
    main()
