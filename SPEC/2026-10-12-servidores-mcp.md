# Servidor MCP do CircuitCrash: partida e ranking

**Data:** 12/10/2026 · **Status:** corrigida e implementada em 12/10/2026, aguardando revisão no PR #11 · **Branch:** `011-servidores-mcp` · **Detalhes:** `specs/011-servidores-mcp/`

## O quê
Um servidor MCP (Model Context Protocol), `circuitcrash`, que deixa um agente de IA, como o Claude Code, operar o CircuitCrash:

- **Consultar** (leitura): o ranking, a posição de um jogador e o placar da partida em andamento.
- **Jogar** (escrita): iniciar a partida de demonstração como um jogador do ranking, colocar ou girar peças e passar a vez. No fim, o resultado é gravado como no site: Fagulhas, rating, partidas e vitórias.

O `.mcp.json` e as permissões do projeto ficam versionados: o agente lê sem pedir licença e pede licença antes de cada escrita. O uso pelo agente fica registrado em `diario/2026-10-08.md`.

## Por quê
É o exercício "um servidor MCP para a AP1": o agente precisa operar a aplicação (num jogo, iniciar partida, jogar e consultar o placar) com pelo menos três tools, uma de leitura e uma de escrita. A primeira versão desta spec, do mesmo dia, leu o pedido como três servidores só de leitura e foi corrigida: o servidor de ranking já feito vira a parte de leitura deste servidor único.

## Critérios de aceitação
1. **Dado** o banco com os dados de exemplo, **quando** peço o ranking ou a posição de um jogador, **então** recebo os mesmos números da tela `/ranking`; um provisório mostra quantas partidas faltam.
2. **Dado** um apelido, **quando** inicio a partida, **então** começa a partida de demonstração da tela `/partida`, jogando como "Você" por esse jogador.
3. **Dado** uma partida em andamento, **quando** consulto, **então** recebo rodada, placar, peças da mão, casas ocupadas e jogadas válidas.
4. **Dado** uma jogada que não liga no meu circuito, **então** ela é recusada com o motivo e não gasta a vez.
5. **Dado** o fim da partida, **então** o resultado é gravado uma única vez, com as mesmas regras do site, e a resposta mostra colocação, Fagulhas e rating antes e depois.
6. As tools de leitura estão em `allow` e as de escrita em `ask`; cada docstring diz quando usar a tool.
7. O diário registra a tarefa, as tools escolhidas, os erros do agente e a perna da tríade.
8. Nenhuma resposta traz e-mail; apelido inexistente ou partida não iniciada respondem sem erro.
9. Testes contra memória e banco; `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Perfil e loja pelo MCP, comprar avatar ou mudar dados fora da partida.
- Várias partidas ao mesmo tempo, partidas entre pessoas e os adversários automáticos (spec 010).
- Login no servidor e publicação na internet.
