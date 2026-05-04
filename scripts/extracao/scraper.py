import asyncio
import aiohttp
import time
from datetime import datetime

import config
from database import DatabaseManager, clean_value


def log(msg):
    """Função simples de log com timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


_projetos_debug_logged = False


def extrair_financiadores_do_projeto(proj, participacao=None):
    """Extrai somente nomes válidos de financiadores. Se não houver, retorna None."""
    encontrados = []

    def adicionar(texto):
        if not isinstance(texto, str):
            return
        texto = texto.strip()
        if not texto:
            return
        if not any(c.isalpha() for c in texto):
            return
        if texto not in encontrados:
            encontrados.append(texto)

    def visitar(item):
        if item is None:
            return

        if isinstance(item, str):
            adicionar(item)
            return

        if isinstance(item, list):
            for subitem in item:
                visitar(subitem)
            return

        if isinstance(item, dict):
            for chave in (
                "nomeInstituicao",
                "nomeFinanciador",
                "financiadorDoProjeto",
                "instituicao",
                "nome",
                "sigla",
            ):
                if chave in item:
                    visitar(item.get(chave))
            return

    visitar((proj or {}).get("financiadoresDoProjeto"))
    visitar((proj or {}).get("financiadorDoProjeto"))

    if participacao is not None:
        visitar((participacao or {}).get("financiadoresDoProjeto"))
        visitar((participacao or {}).get("financiadorDoProjeto"))

    return "; ".join(encontrados) if encontrados else None


def _collect_strings(value):
    """Coleta recursivamente strings de listas/dicts para inspeção textual."""
    values = []
    if value is None:
        return values
    if isinstance(value, str):
        text = value.strip()
        if text:
            values.append(text)
        return values
    if isinstance(value, dict):
        for v in value.values():
            values.extend(_collect_strings(v))
        return values
    if isinstance(value, list):
        for item in value:
            values.extend(_collect_strings(item))
        return values
    text = str(value).strip()
    if text:
        values.append(text)
    return values


def eh_projeto_instituto_federal(*objs):
    """Retorna True se houver indícios textuais de vínculo com Instituto Federal."""
    texto = " ".join(_collect_strings(list(objs))).lower()
    if not texto:
        return False

    palavras_validas = [
        "instituto federal",
        "instituto federal goiano",
        "instituto federal de goiás",
        "instituto federal de educação, ciência e tecnologia",
        "if goiano", "ifg", "ifb", "ifac", "ifam", "ifap", "ifba", "ifbaiano",
        "ifc", "ifce", "iff", "iffar", "ifes", "ifma", "ifmg", "ifms", "ifmt",
        "ifnmg", "ifpb", "ifpe", "ifpi", "ifrj", "ifrn", "ifro", "ifrr", "ifrs",
        "ifsc", "ifsp", "ifs", "ifsudeste", "ifsul", "ifsuldeminas", "iftm", "ifto"
    ]
    return any(p in texto for p in palavras_validas)


def _formatar_data(mes, ano):
    ano = clean_value(ano)
    mes = clean_value(mes)
    if not ano:
        return None
    if mes and mes.isdigit():
        return f"{ano}-{int(mes):02d}"
    return ano


def extrair_periodo_projeto(proj, participacao=None):
    """
    Extrai data de início e fim do projeto.

    O Integra costuma expor esses campos em `participacaoEmProjeto`
    (`mesInicio`, `anoInicio`, `mesFim`, `anoFim`) e/ou no próprio
    `projetoDePesquisa` (`anoInicio`, `anoFim`).
    """
    fontes = [participacao or {}, proj or {}]

    def pick(*keys):
        for fonte in fontes:
            if not isinstance(fonte, dict):
                continue
            for key in keys:
                valor = clean_value(fonte.get(key))
                if valor:
                    return valor
        return None

    data_inicio = (
        pick("dataInicio", "inicio", "inicioProjeto")
        or _formatar_data(pick("mesInicio"), pick("anoInicio"))
    )
    data_fim = (
        pick("dataFim", "fim", "fimProjeto")
        or _formatar_data(pick("mesFim"), pick("anoFim"))
    )

    return data_inicio, data_fim


async def fetch_professores(sigla, base_url, db_manager, progress_callback=None):
    """Busca a lista de todos os professores de uma instituição."""
    list_url = f"{base_url}/api/portfolio/pessoa/data"
    professores = []
    start = 0
    total = 1

    if progress_callback:
        progress_callback(0, "?")

    async with aiohttp.ClientSession() as session:
        while True:
            params = {"start": start, "length": config.PAGE_SIZE}
            try:
                async with session.get(list_url, params=params, headers=config.DEFAULT_HEADERS, ssl=False) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
            except Exception as e:
                log(f"[{sigla}] Erro ao buscar lista de professores (start={start}): {e}")
                break

            if not isinstance(data, list) or len(data) < 2 or not data[1]:
                break

            meta, batch = data[0] or {}, data[1] or []
            total = meta.get("total", total)
            length_returned = meta.get("length", len(batch)) or len(batch)

            for p in batch:
                if not isinstance(p, dict):
                    continue
                slug = p.get("slug")
                if slug:
                    professores.append({
                        "nome": p.get("nome"),
                        "campus": p.get("campusNome"),
                        "cargo": p.get("cargo"),
                        "slug": slug,
                        "url_final": f"{base_url}/portfolio/pessoas/{slug}",
                    })

            log(f"[{sigla}] [{len(professores)}/{total}] - professores coletados")
            if progress_callback:
                progress_callback(len(professores), total)

            if len(professores) >= total:
                break

            start += length_returned
            await asyncio.sleep(0.05)

    if professores:
        db_manager.save_professores(sigla, professores)
    return professores


async def _fetch_detail(session, detail_url, p):
    """Busca o detalhe de um único professor."""
    slug = p["slug"]
    start_time = time.perf_counter()

    max_retries = 3
    backoff_base = 1.0

    for attempt in range(1, max_retries + 1):
        try:
            async with session.get(f"{detail_url}/{slug}", headers=config.DEFAULT_HEADERS, ssl=False) as resp:
                if resp.status == 429:
                    retry_after = resp.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else backoff_base * attempt
                    log(f"[{p.get('sigla')}] 429 rate limit para {slug} (tentativa {attempt}/{max_retries}), aguardando {delay:.1f}s")
                    await asyncio.sleep(delay)
                    continue

                if resp.status >= 400:
                    elapsed = time.perf_counter() - start_time
                    return slug, p, {"erro": f"HTTP {resp.status}"}, elapsed

                data = await resp.json()
                elapsed = time.perf_counter() - start_time
                return slug, p, data, elapsed

        except Exception as e:
            if attempt == max_retries:
                elapsed = time.perf_counter() - start_time
                return slug, p, {"erro": str(e)}, elapsed
            await asyncio.sleep(backoff_base * attempt)

    elapsed = time.perf_counter() - start_time
    return slug, p, {"erro": "Max retries exceeded"}, elapsed


async def fetch_detalhes(sigla, base_url, uf, professores, db_manager, progress_callback=None, progress_callback_art=None):
    """Busca os detalhes (TCCs, artigos e projetos) para uma lista de professores."""
    if not professores:
        log(f"[{sigla}] Nenhum professor para buscar detalhes.")
        return

    detail_url = f"{base_url}/api/portfolio/pessoa/s"
    connector = aiohttp.TCPConnector(limit=config.MAX_CONCURRENT)
    completed = 0
    total = len(professores)
    art_count = 0
    proj_count = 0

    log(f"[{sigla}] Coletando detalhes de {total} professores...")
    if progress_callback:
        progress_callback(0, total)
    if progress_callback_art:
        progress_callback_art(0, "?")

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_fetch_detail(session, detail_url, {**p, "sigla": sigla}) for p in professores]

        for coro in asyncio.as_completed(tasks):
            slug, prof, data, elapsed = await coro
            completed += 1

            if not isinstance(data, dict):
                log(f"[{sigla}] detalhe inválido para {slug}: {data}")
                if progress_callback:
                    progress_callback(completed, total)
                continue

            log(f"[{sigla}] [{completed}/{total}] - {slug} -> {elapsed:.2f}s")
            if progress_callback:
                progress_callback(completed, total)

            professor_id = db_manager.get_professor_id(sigla, slug)
            if professor_id is None:
                log(f"[{sigla}] professor_id não encontrado para slug={slug}; registros desse professor serão ignorados.")
                continue

            tccs_para_salvar = []
            artigos_para_salvar = []
            projetos_para_salvar = []

            outra_producao = (data or {}).get("outraProducao") or {}
            if isinstance(outra_producao, dict) and "orientacoesConcluidas" in outra_producao:
                for item in outra_producao.get("orientacoesConcluidas", []):
                    if not isinstance(item, dict):
                        continue

                    for trabalho in item.get("outrasOrientacoesConcluidas", []):
                        if not isinstance(trabalho, dict):
                            continue

                        dados_basicos = trabalho.get("dadosBasicosDeOutrasOrientacoesConcluidas") or {}
                        detalhamento = trabalho.get("detalhamentoDeOutrasOrientacoesConcluidas") or {}

                        natureza = (dados_basicos.get("natureza") or "").upper()
                        if "TRABALHO_DE_CONCLUSAO" not in natureza:
                            continue

                        nome_professor = clean_value(prof.get("nome"))
                        autores = clean_value(detalhamento.get("nomeDoOrientado"))
                        if nome_professor:
                            autores = (autores + ", " if autores else "") + f"{nome_professor} (Orientador/a)"

                        palavras = trabalho.get("palavrasChave") or {}
                        info_add = trabalho.get("informacoesAdicionais") or {}

                        tccs_para_salvar.append((
                            professor_id,
                            slug,
                            nome_professor,
                            prof.get("sigla"),
                            clean_value(detalhamento.get("nomeDaInstituicao")),
                            uf,
                            clean_value(prof.get("campus")),
                            clean_value(dados_basicos.get("ano")),
                            clean_value(detalhamento.get("nomeDoCurso")),
                            autores,
                            clean_value(dados_basicos.get("titulo") or detalhamento.get("titulo")),
                            clean_value(info_add.get("descricaoInformacoesAdicionais")),
                            clean_value(palavras.get("palavrasChaves"))
                        ))

            prodbib = (data or {}).get("producaoBibliografica") or {}
            if isinstance(prodbib, dict):
                for bloco in prodbib.get("artigosPublicados", []):
                    if not isinstance(bloco, dict):
                        continue

                    for art in bloco.get("artigoPublicado", []):
                        if not isinstance(art, dict):
                            continue

                        dados = art.get("dadosBasicosDoArtigo") or {}
                        titulo_art = dados.get("tituloDoArtigo") or dados.get("titulo")
                        ano_art = dados.get("anoDoArtigo") or dados.get("ano")
                        palavras = art.get("palavrasChave") or {}
                        detalhamento_art = art.get("detalhamentoDoArtigo") or {}
                        journal = detalhamento_art.get("tituloDoPeriodicoOuRevista")
                        doi = dados.get("doi")
                        nome_professor = clean_value(prof.get("nome"))

                        if titulo_art:
                            artigos_para_salvar.append((
                                professor_id,
                                slug,
                                nome_professor,
                                prof.get("sigla"),
                                clean_value(ano_art),
                                clean_value(titulo_art),
                                clean_value(journal),
                                clean_value(doi),
                                clean_value(palavras.get("palavrasChaves"))
                            ))

            global _projetos_debug_logged
            dados_gerais = (data or {}).get("dadosGerais") or {}
            atuacoes_prof = dados_gerais.get("atuacoesProfissionais") or {}
            atuacoes = atuacoes_prof.get("atuacaoProfissional") or []

            if not _projetos_debug_logged:
                if not atuacoes:
                    log(f"[{sigla}] dadosGerais/atuacoesProfissionais ausente ou vazio")
                else:
                    log(f"[{sigla}] encontrado dadosGerais/atuacoesProfissionais com {len(atuacoes)} entradas")
                _projetos_debug_logged = True

            for atuacao in atuacoes:
                if not isinstance(atuacao, dict):
                    continue

                for atividade in atuacao.get("atividadesDeParticipacaoEmProjeto", []):
                    if not isinstance(atividade, dict):
                        continue

                    for participacao in atividade.get("participacaoEmProjeto", []):
                        if not isinstance(participacao, dict):
                            continue

                        for proj in participacao.get("projetoDePesquisa", []):
                            if not isinstance(proj, dict):
                                continue

                            titulo_proj = proj.get("nomeDoProjeto") or proj.get("nomeDoProjetoIngles")
                            descricao = proj.get("descricaoDoProjeto") or proj.get("descricaoDoProjetoIngles")
                            natureza = proj.get("natureza")
                            data_inicio, data_fim = extrair_periodo_projeto(proj, participacao)

                            equipe = []
                            equipe_obj = proj.get("equipeDoProjeto") or {}
                            for integrante in (equipe_obj.get("integrantesDoProjeto") or []):
                                if not isinstance(integrante, dict):
                                    continue
                                nome = integrante.get("nomeParaCitacao") or integrante.get("nomeCompleto")
                                if not nome:
                                    continue
                                if str(integrante.get("flagResponsavel") or "").upper() in ("SIM", "S", "TRUE", "1"):
                                    nome = f"{nome} (Responsável)"
                                equipe.append(nome)
                            equipe_str = "; ".join(equipe)

                            financiadores_str = clean_value(
                                extrair_financiadores_do_projeto(proj, participacao)
                            )
                            nome_professor = clean_value(prof.get("nome"))

                            if not eh_projeto_instituto_federal(atuacao, atividade, participacao, proj):
                                continue

                            if titulo_proj:
                                projetos_para_salvar.append((
                                    professor_id,
                                    slug,
                                    nome_professor,
                                    prof.get("sigla"),
                                    clean_value(titulo_proj),
                                    clean_value(descricao),
                                    clean_value(natureza),
                                    clean_value(equipe_str),
                                    clean_value(financiadores_str),
                                    clean_value(data_inicio),
                                    clean_value(data_fim),
                                ))

            if tccs_para_salvar:
                db_manager.save_tccs(tccs_para_salvar)
            if artigos_para_salvar:
                db_manager.save_artigos(artigos_para_salvar)
                art_count += len(artigos_para_salvar)
                log(f"[{sigla}] {len(artigos_para_salvar)} artigos salvos")
                if progress_callback_art:
                    progress_callback_art(art_count, "?")
            if projetos_para_salvar:
                db_manager.save_projetos(projetos_para_salvar)
                proj_count += len(projetos_para_salvar)
                log(f"[{sigla}] {len(projetos_para_salvar)} projetos salvos")

    log(f"[{sigla}] Todos os TCCs salvos.")
    if progress_callback_art:
        log(f"[{sigla}] Total de artigos coletados: {art_count}")
        log(f"[{sigla}] Total de projetos coletados: {proj_count}")


async def run_for_institution(sigla, base_url, uf, db_manager, callbacks):
    """Executa o pipeline completo para uma instituição."""
    log(f"=== {sigla}: Iniciando coleta ===")

    professores = await fetch_professores(sigla, base_url, db_manager, callbacks.get('prof_progress'))
    log(f"[{sigla}] Total de professores encontrados: {len(professores)}")

    await fetch_detalhes(sigla, base_url, uf, professores, db_manager, callbacks.get('det_progress'), callbacks.get('art_progress'))

    log(f"=== {sigla}: Coleta concluída ===")
