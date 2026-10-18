"""Porteiro do loop da contagem de linhas (spec 013).

Confere se a seção "Contagem de linhas" do README está igual ao cloc de agora e se só o README mudou.
Não muda nenhum arquivo.

    CLOC_PL=/caminho/cloc-2.10.pl uv run python loop/conferir.py
    CLOC_PL=/caminho/cloc-2.10.pl uv run python loop/conferir.py --cloc   # só mostra as tabelas do cloc

Saída: 0 = passou; 1 = não passou, tentar de novo; 2 = escalar para a dupla.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

PASSOU, TENTAR_DE_NOVO, ESCALAR = 0, 1, 2

RAIZ = Path(__file__).resolve().parent.parent
TITULO = "## Contagem de linhas"
# Comando do enunciado da AP1. O código leva "tests" a mais no --exclude-dir; os testes usam o mesmo filtro em tests/.
EXCLUIR_DIR = "node_modules,vendor,dist,build,prompts"
FILTROS = ["--exclude-lang=Markdown,JSON,YAML,CSV,Text,SVG", r"--not-match-f=(lock|\.min\.)", "--quiet"]
LINHAS_DA_TABELA = {"codigo": "| Código", "testes": "| Testes", "total": "| **Total**"}
NOMES = {"codigo": "Código", "testes": "Testes", "total": "Total"}


def secao(readme: str) -> str | None:
    """Do título "## Contagem de linhas" até o próximo título de nível 2."""
    inicio = readme.find(f"\n{TITULO}\n")
    if inicio == -1:
        return None
    resto = readme[inicio + 1 :]
    fim = resto.find("\n## ", len(TITULO))
    return resto if fim == -1 else resto[: fim + 1]


def _numero(texto: str) -> int:
    return int(re.sub(r"\D", "", texto))


def ler_tabela(texto: str) -> dict[str, int]:
    """Números da tabela, com ponto de milhar ("2.965")."""
    numeros: dict[str, int] = {}
    for linha in texto.splitlines():
        for chave, comeco in LINHAS_DA_TABELA.items():
            if linha.startswith(comeco):
                numeros[chave] = _numero(linha.split("|")[2])
    return numeros


def ler_bloco(texto: str, titulo: str) -> str | None:
    """Conteúdo do bloco de código logo depois de um título de nível 3."""
    achado = re.search(rf"^### {re.escape(titulo)}\n```\n(.*?)\n```", texto, re.MULTILINE | re.DOTALL)
    return achado.group(1) if achado else None


def ler_data(texto: str) -> str | None:
    achado = re.search(r"Contado em (\d{2}/\d{2}/\d{4})", texto)
    return achado.group(1) if achado else None


def tabela_do_cloc(saida: str) -> str:
    """A tabela do cloc, sem a linha de cabeçalho com o tempo, que ele imprime mesmo com --quiet."""
    linhas = [linha.rstrip() for linha in saida.strip().splitlines()]
    tracos = [i for i, linha in enumerate(linhas) if linha.startswith("---")]
    return "\n".join(linhas[tracos[0] : tracos[-1] + 1]) if tracos else ""


def soma(saida: str) -> int:
    for linha in saida.splitlines():
        if linha.startswith("SUM:"):
            return int(linha.split()[-1])
    raise ValueError("saída do cloc sem a linha SUM")


def arquivos_extras(porcelana: str) -> list[str]:
    """Arquivos mudados ou novos, em git status --porcelain, além do README.md."""
    caminhos = [linha[3:].strip().strip('"') for linha in porcelana.splitlines() if linha.strip()]
    return [caminho for caminho in caminhos if caminho != "README.md"]


def avaliar(
    readme: str, readme_antes: str, cloc_codigo: str, cloc_testes: str, porcelana: str, hoje: date
) -> tuple[int, list[str]]:
    """Decide o resultado da volta. Escalar vence tentar de novo."""
    texto = secao(readme)
    if texto is None:
        return ESCALAR, [f'O README não tem a seção "{TITULO}".']
    try:
        agora = {"codigo": soma(cloc_codigo), "testes": soma(cloc_testes)}
    except ValueError as erro:
        return ESCALAR, [f"O cloc não rodou direito: {erro}."]
    agora["total"] = agora["codigo"] + agora["testes"]

    escalar: list[str] = []
    anterior = secao(readme_antes)
    antes = ler_tabela(anterior) if anterior else {}
    for chave in ("codigo", "testes"):
        if chave in antes and agora[chave] < antes[chave]:
            escalar.append(f"A contagem de {NOMES[chave]} caiu de {antes[chave]} para {agora[chave]}: código apagado?")
    if escalar:
        return ESCALAR, escalar

    problemas: list[str] = []
    tabela = ler_tabela(texto)
    for chave, esperado in agora.items():
        lido = tabela.get(chave)
        if lido != esperado:
            problemas.append(f"Tabela, linha {NOMES[chave]}: o README diz {lido}, o cloc dá {esperado}.")
    for titulo, saida in (("Código", cloc_codigo), ("Testes", cloc_testes)):
        bloco = ler_bloco(texto, titulo)
        if bloco is None or [linha.rstrip() for linha in bloco.splitlines()] != tabela_do_cloc(saida).splitlines():
            problemas.append(f"O bloco de ### {titulo} não é igual à tabela do cloc.")
    data = ler_data(texto)
    if data != hoje.strftime("%d/%m/%Y"):
        problemas.append(f'A linha "Contado em" diz {data}; precisa ser {hoje:%d/%m/%Y}.')
    extras = arquivos_extras(porcelana)
    if extras:
        problemas.append(f"Só o README.md pode mudar; mudaram também: {', '.join(extras)}.")
    return (TENTAR_DE_NOVO if problemas else PASSOU), problemas


def mostrar_cloc(cloc_codigo: str, cloc_testes: str) -> str:
    """As duas tabelas do cloc e as somas, prontas para copiar para o README."""
    codigo, testes = soma(cloc_codigo), soma(cloc_testes)
    linhas = [
        f"Código (sem tests/): {codigo}",
        f"Testes (tests/): {testes}",
        f"Total: {codigo + testes}",
        "",
        "### Código",
        tabela_do_cloc(cloc_codigo),
        "",
        "### Testes",
        tabela_do_cloc(cloc_testes),
    ]
    return "\n".join(linhas)


def _rodar(*comando: str) -> str:
    return subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")  # o console do Windows usa cp1252
    cloc_pl = os.environ.get("CLOC_PL", "")
    if not cloc_pl or not Path(cloc_pl).is_file():
        print("ESCALAR: defina CLOC_PL com o caminho do cloc-2.10.pl (o cloc não está instalado).")
        return ESCALAR
    try:
        cloc_codigo = _rodar("perl", cloc_pl, ".", "--vcs=git", f"--exclude-dir={EXCLUIR_DIR},tests", *FILTROS)
        cloc_testes = _rodar("perl", cloc_pl, "tests", "--vcs=git", f"--exclude-dir={EXCLUIR_DIR}", *FILTROS)
        if "--cloc" in sys.argv[1:]:
            print(mostrar_cloc(cloc_codigo, cloc_testes))
            return PASSOU
        porcelana = _rodar("git", "status", "--porcelain")
        readme_antes = _rodar("git", "show", "HEAD:README.md")
    except (OSError, subprocess.CalledProcessError) as erro:
        print(f"ESCALAR: um comando falhou: {erro}")
        return ESCALAR
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")

    codigo, problemas = avaliar(readme, readme_antes, cloc_codigo, cloc_testes, porcelana, date.today())
    print({PASSOU: "PASSOU", TENTAR_DE_NOVO: "NÃO PASSOU (tentar de novo)", ESCALAR: "ESCALAR"}[codigo])
    for problema in problemas:
        print(f"- {problema}")
    print(f"cloc agora: código {soma(cloc_codigo)}, testes {soma(cloc_testes)}.")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
