# Plano — 010 Adversários automáticos

**Spec:** [spec.md](spec.md) · **Data:** 06/10/2026

## Resumo
A estratégia dos adversários fica num módulo novo, `domain/adversarios.py`, em Python puro. Ele lista as jogadas válidas de um jogador, escolhe a jogada "médio" simulando cada colocação e cada giro numa cópia do tabuleiro, e aplica a jogada escolhida. `tabuleiro.py` ganha as mãos dos adversários e a semente da partida, e o fim do turno do jogador humano passa a chamar `adversarios.jogar_adversarios` antes de a rodada avançar. `app.py` e as rotas não mudam; a tela só troca o aviso de que os adversários estão parados.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| Regras | `domain/adversarios.py` e `domain/tabuleiro.py`, sem banco, rede nem relógio (constituição III) |
| Sorteio | `nova_partida(semente=42)`; peças e desempates usam `estado.sorteio` |
| Dados | Nenhuma mudança no `Repositorio` nem no banco |
| Testes | pytest; `tests/test_adversarios.py` novo; ajustes em `tests/test_tabuleiro.py` e `tests/test_paginas.py` |

## Checagem da constituição
- I Python: ok.
- II Spec antes de código: spec commitada antes; plano e tarefas também, antes do código.
- III Regras isoladas: `adversarios.py` só importa `tabuleiro`; todo sorteio vem de `estado.sorteio`, criado com a semente.
- IV Contrato de dados: não muda.
- V Servidor decide: os adversários jogam no servidor, dentro da mesma requisição da jogada humana.
- VI Celular: só muda um texto da tela.
- VII Qualidade: testes novos para validade, semente e partida completa.

## Estrutura
```text
src/circuitcrash/
├── domain/
│   ├── tabuleiro.py      # semente, maos_adversarios, _encosta_no_circuito por jogador, fim do turno chama os adversários, bônus final para os quatro
│   └── adversarios.py    # novo: Jogada, jogadas_validas, eh_valida, escolher_jogada, aplicar, jogar_adversarios
└── web/templates/
    └── partida.html      # aviso: "Lia, Bruno e Kai jogam logo depois de você."
tests/
├── test_adversarios.py   # novo
├── test_tabuleiro.py     # rodada avança uma vez por jogada humana, mãos dos adversários
└── test_paginas.py       # valores do fim de partida com os adversários jogando
```

## Regras (`domain/adversarios.py`)
```python
@dataclass(frozen=True)
class Jogada:
    tipo: TipoJogada            # COLOCAR, GIRAR ou PASSAR
    linha: int = -1
    coluna: int = -1
    indice: int = -1            # peça da mão (só COLOCAR)
    saidas: str = ""            # orientação escolhida (só COLOCAR)

def jogadas_validas(estado, jogador) -> list[Jogada]
def eh_valida(estado, jogador, jogada) -> bool
def escolher_jogada(estado, jogador) -> Jogada
def aplicar(estado, jogador, jogada) -> str   # devolve a linha do histórico
def jogar_adversarios(estado) -> None          # jogadores 1, 2, 3
```
- **Colocar:** cada peça da mão em cada orientação distinta, em cada casa vazia em que ela se liga a uma saída de uma casa do circuito do jogador (a mesma regra do jogador humano, agora com o jogador como parâmetro).
- **Girar:** peças do próprio jogador (giro de 90° no sentido horário).
- **Passar:** sempre válida.
- **Simulação:** copia casas e pontos para um `EstadoPartida` novo, aplica a jogada e chama `recalcular`. Ganho = pontos do jogador depois − antes.
- **Distância até o alvo (`distancia_do_alvo`):** busca em largura pelas casas vazias, a partir das que recebem uma saída livre do circuito, até uma casa vizinha ao alvo (o número de peças que faltam, sem olhar o formato). O alvo é a fonte; com o circuito energizado, os objetivos que ele ainda não toca. `SEM_CAMINHO` quando não há caminho.
- **Escolha:** colocações com ganho > 0 ou progresso maior que o atual, pela chave `(ganho, energizado, -distância)`; senão, giros com ganho > 0 ou circuito maior, sem perder a energia, pela chave `(ganho, energizado, tamanho)`; senão, passar. Entre as jogadas de mesma chave, `estado.sorteio.choice`.
- **Aplicar:** colocar tira a peça da mão e compra outra do sorteio; depois `recalcular`. O histórico ganha "Lia colocou uma curva", "Bruno girou a sua peça" ou "Kai passou a vez", seguido das capturas, se houver.

## Mudanças em `tabuleiro.py`
- `EstadoPartida.maos_adversarios: dict[int, list[PecaMao]]`.
- `nova_partida(semente: int = 42)`: sorteia a mão do jogador humano primeiro (a mesma de hoje com a semente 42) e depois as dos adversários.
- `_encosta_no_circuito(estado, linha, coluna, saidas, jogador=0)`.
- `_fim_do_turno`: registra a jogada humana, chama `adversarios.jogar_adversarios` (import dentro da função, porque `adversarios` importa `tabuleiro`), avança a rodada e, no fim, dá +3 a todo jogador energizado, como dizem as regras. O histórico guarda as 8 linhas mais recentes (duas rodadas).

## Testes
- `test_adversarios.py`: em várias sementes, com o jogador humano jogando pela mesma estratégia, toda jogada escolhida por um adversário está em `jogadas_validas` e passa em `eh_valida`, e a peça colocada fica no circuito dele; prefere a captura que vale mais; coloca para se aproximar da fonte; passa quando nada ajuda; mesma semente, mesma partida (histórico, pontos e casas); sementes diferentes podem divergir; partida de 12 rodadas (a partir da rodada 1) termina com classificação de 4 e o histórico tem linhas dos três adversários.
- `test_tabuleiro.py`: uma jogada aceita avança a rodada uma vez e põe as linhas dos adversários no histórico; jogada recusada não aciona os adversários.
- `test_paginas.py`: atualizar a colocação, as Fagulhas e o rating esperados do fim de partida.

## Decisões
- **Distância por caminho de casas vazias, e não em linha reta, e o alvo muda depois de energizar:** com a distância em linha reta até a fonte, no tabuleiro da demonstração os três adversários passavam a partida inteira (Lia e Bruno já começam energizados e Kai está cercado). Contando o caminho livre e mirando o objetivo mais próximo depois da fonte, Bruno avança pela borda e captura o Núcleo.
- **Adversário médio só gira as próprias peças:** é o que a spec pede; girar peça alheia para atrapalhar fica para o nível difícil.
- **Rodada = uma volta dos quatro:** a partida continua com 12 rodadas e os adversários jogam inclusive na última.
- **Bônus final para os quatro:** a tela de regras já diz "+3 se o seu circuito estiver energizado"; antes só o jogador humano recebia porque só ele jogava.

## Riscos
- **Valores do fim de partida nos testes de tela mudam:** são recalculados e o comentário do teste é atualizado.
- **Desempenho:** no máximo 5 peças × 4 orientações × 49 casas simulações por adversário, com tabuleiro 7×7: rápido o bastante para uma requisição.
