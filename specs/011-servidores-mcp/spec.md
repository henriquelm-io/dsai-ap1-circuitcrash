# Spec 011 — Servidor MCP do CircuitCrash: partida e ranking

**Branch:** `011-servidores-mcp` · **Status:** corrigida e implementada em 12/10/2026, aguardando revisão no PR #11 · **Criada em:** 12/10/2026 · **Dono:** Severino · **Origem:** [SPEC/2026-10-12-servidores-mcp.md](../../SPEC/2026-10-12-servidores-mcp.md)

## Contexto
Exercício da disciplina (slide "Exercício: um servidor MCP para a AP1"): **um** servidor MCP ligado à aplicação da AP1, para o agente operar a aplicação por ele. O enunciado pede:

1. O servidor fala com a aplicação. Num jogo: iniciar partida, fazer uma jogada, consultar o placar.
2. Pelo menos três tools, com pelo menos uma de leitura e uma de escrita, e docstrings que digam **quando** usar cada uma.
3. O servidor ligado ao agente por um `.mcp.json` versionado, com `allow` para a leitura e `ask` para a escrita, e uma tarefa pedida ao agente que só se resolve usando a aplicação.
4. Um registro em `diario/2026-10-08.md`: quais tools o agente escolheu, onde errou e qual perna da tríade o servidor abre.

**Correção de 12/10:** a primeira versão desta spec leu o pedido como três servidores só de leitura (ranking, perfil e loja), e só o de ranking foi feito. Ele não atendia aos itens 1, 2 (nenhuma escrita), 3 (sem `allow`/`ask`) e 4. Esta versão troca os três servidores por um só, `circuitcrash`, que mantém as duas consultas de ranking e passa a jogar a partida de demonstração. Perfil e loja saem do escopo.

## Histórias de usuário

### H1 — Consultar o ranking (prioridade P1)
Como jogador, quero perguntar ao agente quem lidera e em que posição estou.

Critérios de aceitação:
1. **Dado** o banco com os dados de exemplo, **quando** peço o ranking, **então** recebo os jogadores na ordem da tela `/ranking`, com posição, apelido, rating, partidas, vitórias e taxa de vitória; posso pedir de 1 a 50 (padrão 10), e valores fora disso são ajustados.
2. **Dado** um apelido, **quando** peço a posição, **então** recebo posição e rating, ou, se o jogador é provisório, quantas partidas faltam para entrar no ranking.
3. Apelido sem diferenciar maiúsculas; apelido inexistente responde com mensagem clara, sem erro.

### H2 — Jogar uma partida pelo agente (P1)
Como jogador, quero pedir ao agente que jogue a partida de demonstração por mim, como um jogador do ranking, e ver o resultado no meu perfil.

**Teste independente:** pedir ao agente "jogue uma partida como luma_dev e diga quanto o rating e as Fagulhas mudaram"; conferir em `/perfil` como `luma_dev`.

Critérios de aceitação:
1. **Dado** um apelido, **quando** inicio a partida, **então** começa a mesma partida de demonstração da tela `/partida`, jogando como "Você", e o resultado será gravado para esse jogador. Iniciar de novo descarta a partida em andamento sem gravar.
2. **Dado** uma partida em andamento, **quando** consulto o placar, **então** recebo rodada, rodadas restantes, pontos de cada jogador, quem está energizado, as peças da mão com as saídas, as casas ocupadas do tabuleiro e as jogadas válidas de colocar peça.
3. **Dado** uma peça da mão, um número de giros e uma casa, **quando** jogo, **então** vale a mesma regra da tela: a peça precisa ligar no meu circuito; jogada recusada não gasta a vez e devolve o motivo. Jogar numa casa com peça gira essa peça, como na tela.
4. Posso passar a vez.
5. **Dado** a última rodada, **quando** a partida termina, **então** o resultado é gravado uma única vez, como no site (Fagulhas pela colocação com o limite do dia, rating pelo Elo, partidas, vitórias e objetivos), e a resposta traz colocação, Fagulhas e rating antes e depois.
6. Sem partida iniciada, jogar, passar ou consultar a partida respondem com mensagem clara, sem erro.

### H3 — Permissões e registro (P1)
Como dupla, queremos que o agente leia sem pedir licença, mas peça licença antes de mudar dados, e registrar como ele usou o servidor.

Critérios de aceitação:
1. O `.mcp.json` e as permissões do projeto estão versionados: as tools de leitura em `allow` e as de escrita em `ask`.
2. As docstrings de cada tool dizem quando usá-la.
3. `diario/2026-10-08.md` registra a tarefa pedida, as tools que o agente chamou e em que ordem, onde errou e qual perna da tríade o servidor abre.

## Requisitos funcionais
- **RF-01** Um servidor MCP, `circuitcrash`, iniciado por um comando próprio, com seis tools: leitura `ver_ranking`, `posicao_do_jogador`, `ver_partida`; escrita `iniciar_partida`, `jogar_peca`, `passar_vez`.
- **RF-02** As tools de leitura não mudam dados. As de escrita mudam só a partida em andamento e, no fim dela, gravam o resultado pelo contrato `Repositorio`, sem método novo ou alterado.
- **RF-03** As regras da partida e do resultado são as mesmas do site (`domain/`); o servidor não reimplementa regra de jogo nem de Fagulhas e rating.
- **RF-04** Uma partida por vez no servidor, guardada na memória do processo.
- **RF-05** Banco escolhido como no site: `DATABASE_URL` do `.env`; vazio, dados de exemplo em memória.
- **RF-06** O e-mail dos jogadores não sai em nenhuma resposta.
- **RF-07** Respostas estruturadas, com campos nomeados.

## Critérios de sucesso
- **CS-01** O agente, no Claude Code, termina uma partida pedida em linguagem natural usando só as tools, e o resultado aparece em `/perfil`.
- **CS-02** As leituras rodam sem pedir licença, e cada escrita pede.
- **CS-03** Testes de cada tool contra a memória e o banco, e pelo cliente MCP em processo.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Perfil e loja pelo MCP (eram as partes 2 e 3 da primeira versão).
- Comprar avatar ou mudar dados fora da partida.
- Várias partidas ao mesmo tempo, partidas entre pessoas e os adversários automáticos da spec 010.
- Login ou controle de acesso no servidor: ele roda na máquina de quem usa, sobre o banco local.
- Publicar o servidor na internet.

## Pontos para a revisão (Henrique)
1. **Dependência nova:** `mcp` 2.3 (SDK oficial).
2. **Nenhuma mudança no contrato `Repositorio`.**
3. **Cálculo do resultado da partida de demonstração** (colocação, adversários e objetivos a partir do tabuleiro) sai de `app.py` para `domain/economia.py`, para o site e o MCP usarem a mesma função. O comportamento do site não muda.
