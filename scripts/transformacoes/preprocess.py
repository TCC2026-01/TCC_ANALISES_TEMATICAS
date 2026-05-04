# -*- coding: utf-8 -*-
"""
Preprocess ajustado para:
- melhorar a nomeação dos tópicos (remove "De", "Em", etc.)
- manter suporte a curso_unificado
- manter data_inicio e data_fim em projetos
- funcionar sem gensim
- gerar 3 parquets separados
"""

import json
import re
import sqlite3
import time
from functools import lru_cache
from pathlib import Path

import nltk
import pandas as pd
import spacy
from langdetect import detect
from nltk.corpus import stopwords
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
from unidecode import unidecode

# ---------------- CONFIGURAÇÕES ----------------
PROCESSED_DB_NAME = "datamart.db"

OUTPUT_TCC = r"scripts\interface\tccs_dashboard.parquet"
OUTPUT_ARTIGO = r"scripts\interface\artigos_dashboard.parquet"
OUTPUT_PROJETO = r"scripts\interface\projetos_dashboard.parquet"
TOPIC_DIAGNOSTICS_FILENAME = r"scripts\interface\diagnostico_topicos.csv"

AGRUPAMENTOS_CURSOS_JSON = "agrupamentos_cursos.json"

TCC_TOPIC_RANGE = range(10, 31)
ARTIGO_TOPIC_RANGE = range(5, 21)
PROJETO_TOPIC_RANGE = range(5, 21)

TOPIC_LABELS = {
    "desenvolvimento analise tecnologia": "Desenvolvimento Tecnológico",
    "matematica aprendizagem professores": "Educação Matemática",
    "solo producao sementes": "Agronomia e Produção Agrícola",
}

IGNORED_WORDS = set([
    "apos", "atraves", "assim", "como", "com", "de", "da", "do", "dos", "das",
    "em", "e", "entre", "na", "no", "ou", "por", "sob", "sobre", "partir",
    "nao", "segundo", "dentro", "tendo", "ano", "anos",
    "aluno", "alunos", "brasileira", "ciencia", "coorientacao", "faculdade",
    "if", "ifb", "ifba", "ifg", "ifgo", "instituicao", "instituto", "orientador",
    "pessoa", "professor", "sigla", "universidade", "tecnico", "publica", "federal",
    "avaliacao", "conclusao", "conclusao_de_curso", "consideracoes",
    "dissertacao", "introducao", "metodologia", "objetivo", "objetivos",
    "palavra", "palavras", "projeto", "projetos", "referencias", "resumo",
    "tcc", "trabalho", "comparativo", "artigo", "artigos",
    "ensino", "medio", "superior", "educacao", "profissional",
    "docentes", "docencia", "abordagem", "aspectos", "base", "baseado",
    "banca", "caso", "cursos", "durante", "estrategia", "estrategias",
    "estudo", "eja", "ferramenta", "informacao", "informacoes",
    "licenciatura", "modelagem", "modelo", "modelos", "municipal", "novos",
    "pesquisa", "possiveis", "processo", "processos", "proposta", "propostas",
    "resultado", "tecnica", "tecnicas", "uso", "utilizacao", "usando",
    "perspectiva", "prof", "docente", "formacao", "pedagogica", "didatico",
    "metodos", "problemas", "resolucao", "tema", "sistema", "sistemas", "controle",
    "acerca", "acoes", "acesso", "alternativa", "aplicado", "areas",
    "biologia", "conceitos", "comparativa", "contribuicao", "contribuicoes",
    "contexto", "criancas", "deteccao", "diferentes", "dimensionamento", "elaboracao",
    "ensinoaprendizagem", "experiencia", "foco", "forma", "funcao", "impactos",
    "identificacao", "material", "melhoria", "novo", "novas", "periodo", "presente",
    "prototipo", "reflexoes", "relacoes", "representacao", "sequencia",
    "setor", "simulacao", "utilizando", "visao", "perspectivas", "indicadores", "livros",
    "acre", "alagoas", "amapa", "amazonas", "anapolis", "aparecida", "bahia", "ceara",
    "cidade", "distrito", "espirito", "formosa", "goias", "goiania", "goianiago",
    "jatai", "joao", "maranhao", "mato", "minas", "para", "paraiba", "parana",
    "pernambuco", "piaui", "porto", "rio", "rondonia", "roraima", "salvador",
    "santa", "sergipe", "tocantins", "municipio", "brasil", "brasilia", "campus",
    "brasileiro", "sao", "paulo", "uruacu", "sul", "sudeste", "centrooeste",
    "norte", "nordeste", "centro", "oeste", "estadual",
    "study", "studies", "using", "used", "based", "analysis", "results",
    "paper", "work", "different", "approach", "through", "data",
    "system", "systems", "research", "application", "applications",
    "proposed", "proposal", "evaluation", "process",
])

BAD_TOPIC_WORDS = IGNORED_WORDS.union({
    "de", "da", "do", "dos", "das", "em", "no", "na", "nos", "nas", "ter","em", "e", "ou","a" ,"esse"
    "por", "para", "com", "sem", "entre", "sobre", "and", "the", "from"
})


# ---------------- UTILITÁRIOS ----------------
def setup_nltk():
    try:
        stopwords.words("portuguese")
        stopwords.words("english")
    except LookupError:
        print("--> Baixando recursos do NLTK (stopwords)...")
        nltk.download("stopwords")
        print("--> Download concluído.")


def clean_text_piece(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).replace("&#10;", " ").strip()
    return re.sub(r"\s+", " ", text)


def detect_language(text):
    try:
        if not isinstance(text, str) or not text.strip():
            return "unknown"
        return detect(text)
    except Exception:
        return "unknown"


@lru_cache(maxsize=4)
def get_spacy_model(idioma):
    model_name = "pt_core_news_sm" if idioma == "pt" else "en_core_web_sm"
    lang_code = "pt" if idioma == "pt" else "en"
    try:
        return spacy.load(model_name, disable=["ner", "parser"])
    except Exception:
        return spacy.blank(lang_code)


def get_stop_words(idioma):
    words = set(stopwords.words("english" if idioma == "en" else "portuguese"))
    return {unidecode(w).lower().strip() for w in words if str(w).strip()}


def preprocess_text(text, idioma="pt"):
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()

    nlp = get_spacy_model("en" if idioma == "en" else "pt")
    stop_words = get_stop_words("en" if idioma == "en" else "pt")

    doc = nlp(text)
    tokens = []

    for token in doc:
        if token.is_space or token.is_punct:
            continue

        lemma = token.lemma_.lower().strip() if token.lemma_ else token.text.lower().strip()
        lemma = unidecode(lemma)
        lemma = re.sub(r"[^a-zA-Z\s]", "", lemma).strip()

        if not lemma:
            continue
        if len(lemma) <= 2:
            continue
        if lemma in stop_words:
            continue
        if lemma in IGNORED_WORDS:
            continue

        tokens.append(lemma)

    return " ".join(tokens)


def normalize_topic_key(text):
    text = unidecode(str(text)).lower().strip()
    return re.sub(r"\s+", " ", text)


def normalize_topic_token(token):
    token = unidecode(str(token)).lower().strip()
    token = re.sub(r"[^a-zA-Z\s]", "", token).strip()
    return token


def clean_topic_words(top_words, limit=6):
    cleaned = []
    seen = set()

    for word in top_words:
        for part in str(word).split():
            token = normalize_topic_token(part)

            if not token:
                continue
            if len(token) <= 2:
                continue
            if token in BAD_TOPIC_WORDS:
                continue
            if token in seen:
                continue

            seen.add(token)
            cleaned.append(token)

            if len(cleaned) >= limit:
                return cleaned

    return cleaned


def get_topic_name(topic_idx, top_words, tipo):
    top_words = clean_topic_words(top_words, limit=6)

    if not top_words:
        return f"{tipo} - Tópico {topic_idx}"

    candidate_key = normalize_topic_key(" ".join(top_words[:3]))
    if candidate_key in TOPIC_LABELS:
        return f"{tipo} - {TOPIC_LABELS[candidate_key]}"

    capitalized_words = [word.capitalize() for word in top_words]
    return f"{tipo} - Tópico {topic_idx}: {', '.join(capitalized_words)}"


def escolher_parametros_modelagem(total_docs):
    if total_docs < 50:
        return {"min_df": 1, "max_df": 1.0, "max_features": 1000}
    if total_docs < 300:
        return {"min_df": 2, "max_df": 0.95, "max_features": 1500}
    if total_docs < 1000:
        return {"min_df": 5, "max_df": 0.92, "max_features": 2000}
    return {"min_df": 20, "max_df": 0.90, "max_features": 3000}


def get_table_columns(conn, table_name):
    query = f"PRAGMA table_info({table_name})"
    df_cols = pd.read_sql_query(query, conn)
    return set(df_cols["name"].tolist()) if not df_cols.empty else set()


def carregar_agrupamentos_cursos():
    path = Path(AGRUPAMENTOS_CURSOS_JSON)
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        mapeamento = {}
        for curso_unificado, variantes in data.items():
            mapeamento[normalize_topic_key(curso_unificado)] = curso_unificado
            if isinstance(variantes, list):
                for variante in variantes:
                    mapeamento[normalize_topic_key(variante)] = curso_unificado
        return mapeamento
    except Exception:
        return {}


def aplicar_curso_unificado(df, mapeamento):
    if "curso" not in df.columns:
        df["curso_unificado"] = None
        return df

    def mapear(curso):
        curso_limpo = clean_text_piece(curso)
        if not curso_limpo:
            return curso_limpo
        chave = normalize_topic_key(curso_limpo)
        return mapeamento.get(chave, curso_limpo)

    df["curso_unificado"] = df["curso"].apply(mapear)
    return df


# ---------------- CARGA DE DADOS ----------------
def load_data_from_datamart(db_name):
    print(f"1. Carregando dados do Data Mart '{db_name}'...")
    try:
        with sqlite3.connect(db_name) as conn:
            query_tcc = """
                SELECT
                    t.tcc_id AS registro_id,
                    t.titulo,
                    t.resumo,
                    t.ano,
                    i.sigla AS instituicao,
                    c.nome_curso AS curso,
                    GROUP_CONCAT(p_aluno.nome_pessoa) AS autores,
                    p_orientador.nome_pessoa AS orientador,
                    t.palavras_chaves,
                    NULL AS natureza,
                    NULL AS financiadores,
                    NULL AS veiculo,
                    NULL AS data_inicio,
                    NULL AS data_fim,
                    'TCC' AS tipo
                FROM fato_tcc t
                LEFT JOIN dim_instituicao i ON t.instituicao_id = i.instituicao_id
                LEFT JOIN dim_curso c ON t.curso_id = c.curso_id
                LEFT JOIN ponte_tcc_aluno pta ON t.tcc_id = pta.tcc_id
                LEFT JOIN dim_pessoa p_aluno ON pta.aluno_id = p_aluno.pessoa_id
                LEFT JOIN ponte_tcc_orientador pto ON t.tcc_id = pto.tcc_id
                LEFT JOIN dim_pessoa p_orientador ON pto.orientador_id = p_orientador.pessoa_id
                GROUP BY t.tcc_id
            """
            df_tcc = pd.read_sql_query(query_tcc, conn)

            fato_artigo_cols = get_table_columns(conn, "fato_artigo")
            if fato_artigo_cols:
                artigo_resumo_expr = "a.resumo" if "resumo" in fato_artigo_cols else "''"
                query_art = f"""
                    SELECT
                        a.artigo_id AS registro_id,
                        a.titulo,
                        {artigo_resumo_expr} AS resumo,
                        a.ano,
                        COALESCE(i.sigla, a.sigla) AS instituicao,
                        NULL AS curso,
                        a.nome_professor AS autores,
                        NULL AS orientador,
                        a.palavras_chaves,
                        NULL AS natureza,
                        NULL AS financiadores,
                        a.journal AS veiculo,
                        NULL AS data_inicio,
                        NULL AS data_fim,
                        'Artigo' AS tipo
                    FROM fato_artigo a
                    LEFT JOIN dim_instituicao i ON a.sigla = i.sigla
                """
                df_art = pd.read_sql_query(query_art, conn)
            else:
                df_art = pd.DataFrame()

            fato_projeto_cols = get_table_columns(conn, "fato_projeto")
            if fato_projeto_cols:
                data_inicio_expr = "p.data_inicio" if "data_inicio" in fato_projeto_cols else "NULL"
                data_fim_expr = "p.data_fim" if "data_fim" in fato_projeto_cols else "NULL"
                query_proj = f"""
                    SELECT
                        p.projeto_id AS registro_id,
                        p.titulo,
                        p.descricao AS resumo,
                        NULL AS ano,
                        COALESCE(i.sigla, p.sigla) AS instituicao,
                        NULL AS curso,
                        p.nome_professor AS autores,
                        NULL AS orientador,
                        NULL AS palavras_chaves,
                        p.natureza,
                        p.financiadores,
                        NULL AS veiculo,
                        {data_inicio_expr} AS data_inicio,
                        {data_fim_expr} AS data_fim,
                        'Projeto' AS tipo
                    FROM fato_projeto p
                    LEFT JOIN dim_instituicao i ON p.sigla = i.sigla
                """
                df_proj = pd.read_sql_query(query_proj, conn)
            else:
                df_proj = pd.DataFrame()

        print(f"   - {len(df_tcc)} registros de TCC carregados.")
        if not df_art.empty:
            print(f"   - {len(df_art)} registros de artigos carregados.")
        if not df_proj.empty:
            print(f"   - {len(df_proj)} registros de projetos carregados.")

        return {"TCC": df_tcc, "Artigo": df_art, "Projeto": df_proj}

    except Exception as e:
        print(f"   - ERRO AO CARREGAR DADOS: {e}")
        return None


# ---------------- MODELAGEM ----------------
def montar_texto_analise(row):
    tipo = row.get("tipo", "")
    partes = [clean_text_piece(row.get("titulo"))]

    if tipo == "TCC":
        partes.extend([
            clean_text_piece(row.get("curso_unificado") or row.get("curso")),
            clean_text_piece(row.get("resumo")),
            clean_text_piece(row.get("palavras_chaves")),
        ])
    elif tipo == "Artigo":
        partes.extend([
            clean_text_piece(row.get("resumo")),
            clean_text_piece(row.get("palavras_chaves")),
        ])
    elif tipo == "Projeto":
        partes.extend([
            clean_text_piece(row.get("resumo")),
            clean_text_piece(row.get("natureza")),
        ])
    else:
        partes.extend([
            clean_text_piece(row.get("resumo")),
            clean_text_piece(row.get("palavras_chaves")),
        ])

    texto = " ".join([parte for parte in partes if parte])
    return re.sub(r"\s+", " ", texto).strip()


def fit_lda(df_tipo, tipo, topic_candidates):
    params = escolher_parametros_modelagem(len(df_tipo))
    try:
        vectorizer = TfidfVectorizer(
            max_df=params["max_df"],
            min_df=params["min_df"],
            max_features=params["max_features"],
            ngram_range=(1, 3)
        )
        X = vectorizer.fit_transform(df_tipo["resumo_processado"])
    except ValueError:
        vectorizer = TfidfVectorizer(
            max_df=1.0,
            min_df=1,
            max_features=1000,
            ngram_range=(1, 2)
        )
        X = vectorizer.fit_transform(df_tipo["resumo_processado"])

    if X.shape[0] == 0 or X.shape[1] == 0:
        raise ValueError(f"Não foi possível gerar vocabulário para {tipo}.")

    valid_candidates = [k for k in topic_candidates if 1 <= k <= X.shape[0] and 1 <= k <= X.shape[1]]
    if not valid_candidates:
        valid_candidates = [max(1, min(X.shape[0], X.shape[1]))]

    diagnostics = []
    best_model = None
    best_topic_results = None
    best_k = None
    best_perplexity = None

    for k in valid_candidates:
        lda = LatentDirichletAllocation(n_components=k, random_state=42, n_jobs=-1)
        topic_results = lda.fit_transform(X)
        perplexity = float(lda.perplexity(X))
        score = float(lda.score(X))

        diagnostics.append({
            "tipo": tipo,
            "n_registros": int(X.shape[0]),
            "n_termos": int(X.shape[1]),
            "n_topicos": int(k),
            "perplexidade": perplexity,
            "log_likelihood": score
        })

        if best_perplexity is None or perplexity < best_perplexity:
            best_perplexity = perplexity
            best_model = lda
            best_topic_results = topic_results
            best_k = k

    return vectorizer, best_model, best_topic_results, best_k, diagnostics


def processar_tipo(df_tipo, tipo, mapeamento_cursos):
    if df_tipo.empty:
        return df_tipo.copy(), []

    print(f"2. Processando tipo '{tipo}'...")
    df_tipo = df_tipo.copy()

    if tipo == "TCC":
        df_tipo = aplicar_curso_unificado(df_tipo, mapeamento_cursos)
    else:
        df_tipo["curso_unificado"] = None

    antes_duplicados = len(df_tipo)
    df_tipo = df_tipo.drop_duplicates(subset=["titulo", "instituicao", "ano"])
    print(f"   - Removidos {antes_duplicados - len(df_tipo)} registros duplicados de {tipo}.")

    df_tipo["texto_completo"] = df_tipo.apply(montar_texto_analise, axis=1)

    df_tipo["idioma"] = df_tipo["texto_completo"].apply(detect_language)
    antes_idioma = len(df_tipo)
    df_tipo = df_tipo[df_tipo["idioma"].isin(["pt", "en"])]
    print(f"   - Removidos {antes_idioma - len(df_tipo)} registros de {tipo} por idioma inválido.")

    df_tipo["resumo_processado"] = df_tipo.apply(
        lambda row: preprocess_text(row["texto_completo"], row["idioma"]),
        axis=1
    )

    antes_vazios = len(df_tipo)
    df_tipo = df_tipo[df_tipo["resumo_processado"].astype(str).str.strip() != ""]
    print(f"   - Removidos {antes_vazios - len(df_tipo)} registros vazios de {tipo} após pré-processamento.")
    print(f"   - {len(df_tipo)} registros válidos para {tipo} após limpeza.")

    if df_tipo.empty:
        return df_tipo, []

    if tipo == "TCC":
        topic_candidates = list(TCC_TOPIC_RANGE)
    elif tipo == "Artigo":
        topic_candidates = list(ARTIGO_TOPIC_RANGE)
    else:
        topic_candidates = list(PROJETO_TOPIC_RANGE)

    print(f"   - Testando {tipo} com tópicos de {min(topic_candidates)} a {max(topic_candidates)}.")

    vectorizer, lda, topic_results, best_k, diagnostics = fit_lda(df_tipo, tipo, topic_candidates)
    print(f"   - Melhor configuração para {tipo}: {best_k} tópicos.")

    feature_names = vectorizer.get_feature_names_out()
    topic_name_mapping = {}
    for topic_idx, topic_component in enumerate(lda.components_):
        raw_top_words = [feature_names[i] for i in topic_component.argsort()[:-16:-1]]
        topic_name_mapping[topic_idx] = get_topic_name(topic_idx, raw_top_words, tipo)

    df_tipo["id_topico"] = topic_results.argmax(axis=1)
    df_tipo["nome_topico"] = df_tipo["id_topico"].map(topic_name_mapping)
    df_tipo["n_topicos_modelo"] = best_k
    df_tipo["score_topico"] = topic_results.max(axis=1)

    return df_tipo, diagnostics


# ---------------- SAÍDA ----------------
def salvar_parquet(df, output_filename):
    output_path = Path(output_filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cols_ordenadas = [
        "registro_id", "tipo", "titulo", "autores", "ano", "instituicao",
        "curso", "curso_unificado", "veiculo", "resumo", "palavras_chaves",
        "natureza", "financiadores", "data_inicio", "data_fim",
        "texto_completo", "resumo_processado", "idioma", "id_topico",
        "nome_topico", "n_topicos_modelo", "score_topico", "orientador",
    ]

    for col in cols_ordenadas:
        if col not in df.columns:
            df[col] = None

    df = df[cols_ordenadas]
    df.to_parquet(output_path, index=False)
    print(f"   - Arquivo salvo com sucesso: {output_path}")


def main():
    print("\n--- Iniciando script preprocess.py ---")
    start_time = time.time()

    setup_nltk()
    mapeamento_cursos = carregar_agrupamentos_cursos()
    dados = load_data_from_datamart(PROCESSED_DB_NAME)

    if dados is None:
        print("\nProcesso interrompido. Verifique se o 'datamart.db' foi gerado corretamente.")
        return

    resultados = {}
    diagnosticos = []

    for tipo in ["TCC", "Artigo", "Projeto"]:
        df_tipo = dados.get(tipo, pd.DataFrame())
        df_resultado, diags = processar_tipo(df_tipo, tipo, mapeamento_cursos)
        if not df_resultado.empty:
            resultados[tipo] = df_resultado
        diagnosticos.extend(diags)

    if not resultados:
        print("   - Nenhum dado válido restou após o pré-processamento.")
        return

    print("3. Salvando arquivos parquet separados...")
    if "TCC" in resultados:
        salvar_parquet(resultados["TCC"], OUTPUT_TCC)
    if "Artigo" in resultados:
        salvar_parquet(resultados["Artigo"], OUTPUT_ARTIGO)
    if "Projeto" in resultados:
        salvar_parquet(resultados["Projeto"], OUTPUT_PROJETO)

    if diagnosticos:
        diag_path = Path(TOPIC_DIAGNOSTICS_FILENAME)
        diag_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(diagnosticos).to_csv(diag_path, index=False, encoding="utf-8-sig")
        print(f"   - Diagnóstico de tópicos salvo em: {diag_path}")

    end_time = time.time()
    print(f"\n--- Processo finalizado em {end_time - start_time:.2f} segundos. ---")


if __name__ == "__main__":
    main()
