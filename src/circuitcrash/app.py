"""Aplicação web do CircuitCrash.

Starlette + Jinja2 + HTMX. O FastAPI é construído sobre o Starlette, então estas
rotas podem migrar para ele sem reescrever as telas.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from circuitcrash.dados.config import url_do_banco
from circuitcrash.dados.fabrica import criar_repositorio
from circuitcrash.dados.repositorio import Repositorio
from circuitcrash.domain import economia, loja, tabuleiro
from circuitcrash.domain.economia import LIMITE_DIARIO_FAGULHAS, RECOMPENSA_COLOCACAO
from circuitcrash.domain.modelos import PRECOS, Jogador, Raridade, ResultadoPartida, TipoPartida
from circuitcrash.web import visao

AQUI = Path(__file__).parent
templates = Jinja2Templates(directory=str(AQUI / "web" / "templates"))

JOGADOR_PADRAO = "veterano"

# Partidas de demonstração ficam em memória, uma por navegador.
_partidas: dict[str, tabuleiro.EstadoPartida] = {}
# Resultado gravado de cada partida terminada, com a mesma chave (spec 006).
_resultados: dict[str, ResultadoPartida] = {}


def _repo(request: Request) -> Repositorio:
    repo: Repositorio = request.app.state.repo
    return repo


def _jogador(request: Request) -> Jogador:
    repo = _repo(request)
    jogador = repo.obter_jogador(request.session.get("jogador_id", JOGADOR_PADRAO))
    if jogador is None:
        jogador = repo.obter_jogador(JOGADOR_PADRAO)
    assert jogador is not None
    return jogador


def _render(request: Request, nome: str, pagina: str, **contexto: Any) -> Response:
    repo = _repo(request)
    jogador = _jogador(request)
    avatar = repo.obter_avatar(jogador.avatar_id) if jogador.avatar_id else None
    aviso = request.session.pop("aviso", None)
    return templates.TemplateResponse(
        request,
        nome,
        {
            "pagina": pagina,
            "eu": jogador,
            "meu_avatar": avatar,
            "jogadores_demo": repo.listar_jogadores()[:2],
            "aviso": aviso,
            **contexto,
        },
    )


def _avisar(request: Request, ok: bool, mensagem: str) -> None:
    request.session["aviso"] = {"ok": ok, "texto": mensagem}


# ---------- páginas ----------


async def inicio(request: Request) -> Response:
    repo = _repo(request)
    jogador = _jogador(request)
    return _render(
        request,
        "inicio.html",
        "jogar",
        ranking=repo.ranking(5),
        missoes=repo.missoes_do_dia(jogador.id),
        avatares=repo.listar_avatares(),
    )


async def perfil(request: Request) -> Response:
    repo = _repo(request)
    jogador = _jogador(request)
    meus = repo.inventario(jogador.id)
    avatares = repo.listar_avatares()
    possuidos = [a for a in avatares if a.id in meus]
    proximo = _proximo_avatar(repo, jogador, meus)
    posicao = next((i + 1 for i, j in enumerate(repo.ranking(1000)) if j.id == jogador.id), None)
    return _render(
        request,
        "perfil.html",
        "perfil",
        partidas=repo.partidas_recentes(jogador.id),
        missoes=repo.missoes_do_dia(jogador.id),
        conquistas=repo.conquistas(jogador.id),
        possuidos=possuidos,
        proximo=proximo,
        posicao=posicao,
        preco_comum=PRECOS[Raridade.COMUM],
    )


def _proximo_avatar(repo: Repositorio, jogador: Jogador, meus: set[str]) -> dict[str, Any] | None:
    a_venda = sorted(
        (a for a in repo.listar_avatares() if a.preco is not None and a.id not in meus),
        key=lambda a: a.preco or 0,
    )
    alvo = next((a for a in a_venda if (a.preco or 0) > jogador.fagulhas), None)
    if alvo is None or alvo.preco is None:
        return None
    return {
        "avatar": alvo,
        "falta": alvo.preco - jogador.fagulhas,
        "pct": min(100, round(100 * jogador.fagulhas / alvo.preco)),
    }


async def pagina_loja(request: Request) -> Response:
    repo = _repo(request)
    jogador = _jogador(request)
    meus = repo.inventario(jogador.id)
    filtro = request.query_params.get("raridade", "todos")
    avatares = repo.listar_avatares()
    if filtro != "todos":
        avatares = [a for a in avatares if a.raridade.value == filtro]
    cartoes = []
    for a in avatares:
        if a.id == jogador.avatar_id:
            estado = "em_uso"
        elif a.id in meus:
            estado = "possui"
        elif a.preco is None:
            estado = "exclusivo"
        elif a.preco <= jogador.fagulhas:
            estado = "comprar"
        else:
            estado = "falta"
        cartoes.append({"avatar": a, "estado": estado, "falta": (a.preco or 0) - jogador.fagulhas})
    filtros = [("todos", "Todos")] + [(r.value, r.rotulo) for r in Raridade]
    return _render(
        request,
        "loja.html",
        "loja",
        cartoes=cartoes,
        filtro=filtro,
        filtros=filtros,
        recompensas=RECOMPENSA_COLOCACAO,
        limite_diario=LIMITE_DIARIO_FAGULHAS,
    )


async def comprar(request: Request) -> Response:
    form = await request.form()
    resultado = loja.comprar(_repo(request), _jogador(request).id, str(form.get("avatar_id", "")))
    _avisar(request, resultado.ok, resultado.mensagem)
    return RedirectResponse("/loja", status_code=303)


async def usar(request: Request) -> Response:
    form = await request.form()
    resultado = loja.equipar(_repo(request), _jogador(request).id, str(form.get("avatar_id", "")))
    _avisar(request, resultado.ok, resultado.mensagem)
    destino = str(form.get("voltar", "/loja"))
    return RedirectResponse(destino if destino in ("/loja", "/perfil") else "/loja", status_code=303)


async def ranking(request: Request) -> Response:
    repo = _repo(request)
    return _render(
        request,
        "ranking.html",
        "ranking",
        jogadores=repo.ranking(50),
        avatares={a.id: a for a in repo.listar_avatares()},
    )


async def regras(request: Request) -> Response:
    return _render(
        request,
        "regras.html",
        "regras",
        objetivos=tabuleiro.OBJETIVOS,
        recompensas=RECOMPENSA_COLOCACAO,
        precos=PRECOS,
        limite_diario=LIMITE_DIARIO_FAGULHAS,
    )


async def trocar_jogador(request: Request) -> Response:
    form = await request.form()
    jogador_id = str(form.get("jogador_id", JOGADOR_PADRAO))
    if _repo(request).obter_jogador(jogador_id):
        request.session["jogador_id"] = jogador_id
    referer = request.headers.get("referer", "/")
    return RedirectResponse(referer if referer.startswith(str(request.base_url)) else "/", status_code=303)


async def saude(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


# ---------- partida de demonstração ----------


def _partida(request: Request) -> tabuleiro.EstadoPartida:
    chave = request.session.get("partida_id")
    if not chave or chave not in _partidas:
        chave = secrets.token_hex(8)
        request.session["partida_id"] = chave
        _partidas[chave] = tabuleiro.nova_partida()
    return _partidas[chave]


def _gravar_se_terminou(request: Request, estado: tabuleiro.EstadoPartida) -> bool:
    """Grava o resultado do jogador ativo uma única vez, quando a partida termina.

    Devolve True só na requisição que gravou.
    """
    chave = request.session.get("partida_id")
    if not estado.terminou or not chave or chave in _resultados:
        return False
    repo = _repo(request)
    jogador = _jogador(request)
    classificacao = tabuleiro.classificacao(estado)
    colocacao, _, pontos = next(c for c in classificacao if c[1].indice == 0)
    adversarios = [(economia.RATING_ADVERSARIO_PADRAO, p) for _, j, p in classificacao if j.indice != 0]
    objetivos = sum(1 for linha in estado.casas for casa in linha if casa.capturado_por == 0)
    resultado = economia.resultado_da_partida(
        jogador,
        TipoPartida.RANQUEADA,
        colocacao,
        pontos,
        objetivos,
        adversarios,
        repo.fagulhas_ganhas_hoje(jogador.id),
    )
    repo.registrar_partida(jogador.id, resultado)
    _resultados[chave] = resultado
    return True


def _contexto_partida(request: Request, estado: tabuleiro.EstadoPartida) -> dict[str, Any]:
    jogadores = [
        {"j": j, "pontos": estado.pontos[j.indice], "energizado": tabuleiro.circuito_do_jogador(estado, j.indice)[1]}
        for j in tabuleiro.JOGADORES_DEMO
    ]
    return {
        "estado": estado,
        "casas": visao.casas(estado),
        "mao": visao.mao(estado),
        "jogadores": jogadores,
        "classificacao": tabuleiro.classificacao(estado) if estado.terminou else [],
        "recompensas": RECOMPENSA_COLOCACAO,
        "max_rodadas": tabuleiro.MAX_RODADAS,
        "objetivos": tabuleiro.OBJETIVOS,
        "resultado": _resultados.get(request.session.get("partida_id", "")),
        "limite_diario": LIMITE_DIARIO_FAGULHAS,
    }


async def partida(request: Request) -> Response:
    estado = _partida(request)
    _gravar_se_terminou(request, estado)
    return _render(request, "partida.html", "jogar", **_contexto_partida(request, estado))


async def _responder_jogo(request: Request) -> Response:
    estado = _partida(request)
    gravou = _gravar_se_terminou(request, estado)
    if request.headers.get("hx-request"):
        resposta = templates.TemplateResponse(request, "_jogo.html", _contexto_partida(request, estado))
        if gravou:
            # O cabeçalho fica fora do #jogo: recarrega a página para mostrar as Fagulhas novas.
            resposta.headers["HX-Refresh"] = "true"
        return resposta
    return RedirectResponse("/partida", status_code=303)


def _inteiro(valor: Any, padrao: int = -1) -> int:
    try:
        return int(str(valor))
    except ValueError:
        return padrao


async def acao_selecionar(request: Request) -> Response:
    form = await request.form()
    tabuleiro.selecionar(_partida(request), _inteiro(form.get("indice")))
    return await _responder_jogo(request)


async def acao_girar_mao(request: Request) -> Response:
    tabuleiro.girar_selecionada(_partida(request))
    return await _responder_jogo(request)


async def acao_jogar(request: Request) -> Response:
    form = await request.form()
    tabuleiro.jogar_na_casa(_partida(request), _inteiro(form.get("linha")), _inteiro(form.get("coluna")))
    return await _responder_jogo(request)


async def acao_passar(request: Request) -> Response:
    tabuleiro.passar(_partida(request))
    return await _responder_jogo(request)


async def acao_nova(request: Request) -> Response:
    chave = request.session.get("partida_id")
    if chave:
        _partidas.pop(chave, None)
        _resultados.pop(chave, None)
    _partida(request)
    return await _responder_jogo(request)


def criar_app(repo: Repositorio | None = None) -> Starlette:
    rotas = [
        Route("/", inicio),
        Route("/partida", partida),
        Route("/partida/selecionar", acao_selecionar, methods=["POST"]),
        Route("/partida/girar-mao", acao_girar_mao, methods=["POST"]),
        Route("/partida/jogar", acao_jogar, methods=["POST"]),
        Route("/partida/passar", acao_passar, methods=["POST"]),
        Route("/partida/nova", acao_nova, methods=["POST"]),
        Route("/perfil", perfil),
        Route("/loja", pagina_loja),
        Route("/loja/comprar", comprar, methods=["POST"]),
        Route("/loja/usar", usar, methods=["POST"]),
        Route("/ranking", ranking),
        Route("/regras", regras),
        Route("/jogador", trocar_jogador, methods=["POST"]),
        Route("/health", saude),
        Mount("/static", app=StaticFiles(directory=str(AQUI / "web" / "static")), name="static"),
    ]
    chave = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    app = Starlette(routes=rotas, middleware=[Middleware(SessionMiddleware, secret_key=chave, same_site="lax")])
    # Sem repositório passado: banco se DATABASE_URL estiver preenchida, senão dados em memória.
    app.state.repo = repo or criar_repositorio(url_do_banco())
    return app


app = criar_app()
