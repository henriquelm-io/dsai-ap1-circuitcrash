"""Porteiro do loop da contagem de linhas (spec 013)."""

import importlib.util
from datetime import date
from pathlib import Path
from types import ModuleType

RAIZ = Path(__file__).resolve().parent.parent
HOJE = date(2026, 10, 18)


def _carregar() -> ModuleType:
    especificacao = importlib.util.spec_from_file_location("conferir", RAIZ / "loop" / "conferir.py")
    assert especificacao is not None and especificacao.loader is not None
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


conferir = _carregar()

TRACO = "-" * 79


def _cloc(linhas: list[str], arquivos: int, branco: int, comentario: int, codigo: int) -> str:
    """Saída do cloc 2.10 com --quiet, com o cabeçalho de tempo que ele imprime mesmo assim."""
    return "\n".join(
        [
            "github.com/AlDanial/cloc v 2.10  T=0.05 s (100.0 files/s, 9000.0 lines/s)",
            TRACO,
            "Language                     files          blank        comment           code",
            TRACO,
            *linhas,
            TRACO,
            f"SUM:                     {arquivos:>10} {branco:>14} {comentario:>14} {codigo:>14}",
            TRACO,
            "",
        ]
    )


CLOC_CODIGO = _cloc(
    [
        "Python                          20            500            170           2400",
        "HTML                             9             21              0            600",
    ],
    29,
    521,
    170,
    3000,
)
CLOC_TESTES = _cloc(
    ["Python                          13            482             46           1230"], 13, 482, 46, 1230
)


def _readme(codigo: int = 3000, testes: int = 1230, total: int | None = None, data: str = "18/10/2026") -> str:
    total = codigo + testes if total is None else total
    bloco_codigo = conferir.tabela_do_cloc(CLOC_CODIGO)
    bloco_testes = conferir.tabela_do_cloc(CLOC_TESTES)

    def milhar(n: int) -> str:
        return f"{n:,}".replace(",", ".")

    return f"""# CircuitCrash

## Como rodar
Texto.

## Contagem de linhas
Contado em {data}, às 20:00, com o cloc 2.10 e o comando do enunciado da AP1:

| Parte | Linhas de código |
| --- | --- |
| Código (sem `tests/`) | {milhar(codigo)} |
| Testes (`tests/`) | {milhar(testes)} |
| **Total** | **{milhar(total)}** |

### Código
```
{bloco_codigo}
```

### Testes
```
{bloco_testes}
```

## Publicação
Texto.
"""


ANTES = _readme(2965, 937, data="05/10/2026")


def _avaliar(readme: str, porcelana: str = " M README.md\n", antes: str = ANTES) -> tuple[int, list[str]]:
    resultado: tuple[int, list[str]] = conferir.avaliar(readme, antes, CLOC_CODIGO, CLOC_TESTES, porcelana, HOJE)
    return resultado


def test_le_a_tabela_da_secao() -> None:
    secao = conferir.secao(ANTES)
    assert secao is not None
    assert secao.startswith("## Contagem de linhas")
    assert "## Publicação" not in secao
    assert conferir.ler_tabela(secao) == {"codigo": 2965, "testes": 937, "total": 3902}


def test_soma_do_cloc() -> None:
    assert conferir.soma(CLOC_CODIGO) == 3000
    assert conferir.soma(CLOC_TESTES) == 1230
    assert conferir.tabela_do_cloc(CLOC_TESTES).startswith(TRACO)
    assert "github.com" not in conferir.tabela_do_cloc(CLOC_TESTES)


def test_readme_igual_ao_cloc_passa() -> None:
    assert _avaliar(_readme()) == (0, [])


def test_numero_errado_nao_passa() -> None:
    codigo, problemas = _avaliar(_readme(testes=1229))
    assert codigo == 1
    assert any("Testes" in p and "1229" in p and "1230" in p for p in problemas)


def test_total_que_nao_e_a_soma_nao_passa() -> None:
    codigo, problemas = _avaliar(_readme(total=4000))
    assert codigo == 1
    assert any("Total" in p for p in problemas)


def test_bloco_diferente_do_cloc_nao_passa() -> None:
    readme = _readme().replace("HTML                             9", "HTML                             8")
    codigo, problemas = _avaliar(readme)
    assert codigo == 1
    assert any("### Código" in p for p in problemas)


def test_data_velha_nao_passa() -> None:
    codigo, problemas = _avaliar(_readme(data="17/10/2026"))
    assert codigo == 1
    assert any("18/10/2026" in p for p in problemas)


def test_outro_arquivo_mudado_nao_passa() -> None:
    codigo, problemas = _avaliar(_readme(), " M README.md\n M src/circuitcrash/app.py\n?? loop/rascunho.md\n")
    assert codigo == 1
    assert any("src/circuitcrash/app.py" in p and "loop/rascunho.md" in p for p in problemas)


def test_queda_na_contagem_escala() -> None:
    antes = _readme(3100, 1230, data="05/10/2026")
    codigo, problemas = _avaliar(_readme(), antes=antes)
    assert codigo == 2
    assert any("caiu" in p and "3100" in p for p in problemas)


def test_secao_ausente_escala() -> None:
    codigo, problemas = _avaliar("# CircuitCrash\n\nSem contagem.\n")
    assert codigo == 2
    assert any("Contagem de linhas" in p for p in problemas)
