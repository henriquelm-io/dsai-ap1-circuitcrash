# Servidores MCP: ranking, perfil e loja

**Data:** 12/10/2026 · **Status:** parte 1 (ranking) implementada por Severino; perfil e loja com o Henrique · **Branch:** `011-servidores-mcp` · **Detalhes:** `specs/011-servidores-mcp/`

## O quê
Três servidores MCP (Model Context Protocol) que deixam um assistente de IA, como o Claude Code, consultar os dados do CircuitCrash numa conversa:

- **Ranking:** a classificação dos jogadores e a posição de um jogador.
- **Perfil:** rating, Fagulhas, partidas, vitórias, partidas recentes, missões do dia e conquistas de um jogador.
- **Loja:** os avatares à venda e o que um jogador consegue comprar com as Fagulhas que tem.

Os três só leem. Nenhum deles compra, troca avatar, grava partida ou muda qualquer dado.

## Por quê
O professor pediu três MCPs para o aplicativo. Ranking, perfil e loja são as três áreas com dados reais no banco desde as specs 002 e 006, e respondem perguntas naturais numa conversa: "quem lidera?", "como estou indo?", "o que dá para comprar?". Só ler é mais seguro: um agente não gasta as Fagulhas de ninguém por engano.

## Critérios de aceitação

### Ranking
1. **Dado** o banco com os dados de exemplo, **quando** peço o ranking, **então** recebo os jogadores na mesma ordem da tela `/ranking`, com posição, apelido, rating, partidas e taxa de vitória.
2. Posso pedir só os primeiros N (de 1 a 50; o padrão é 10).
3. **Dado** um apelido, **quando** peço a posição dele, **então** recebo a posição e o rating; se ele ainda está no período provisório, a resposta diz quantas partidas faltam para entrar no ranking.
4. Apelido que não existe dá uma mensagem clara, não um erro.

### Perfil
5. **Dado** um apelido, **quando** peço o perfil, **então** recebo os mesmos números da tela `/perfil`: rating, posição, Fagulhas, partidas, vitórias, taxa de vitória, objetivos capturados, avatar em uso, as 5 partidas mais recentes, as missões do dia e as conquistas.
6. O e-mail do jogador nunca aparece na resposta.

### Loja
7. Posso listar os avatares, com nome, raridade, preço e descrição, filtrando por raridade.
8. **Dado** um apelido, **quando** pergunto o que ele pode comprar, **então** recebo as Fagulhas dele, os avatares que ele já pode comprar e, para os outros à venda, quantas Fagulhas faltam. Avatares que ele já tem e os exclusivos não entram como compráveis.

### Geral
9. Cada servidor roda sozinho e pode ser ligado ao Claude Code pelo arquivo de configuração do projeto.
10. Os servidores usam o mesmo banco do site (`DATABASE_URL` do `.env`); sem banco, usam os dados de exemplo em memória.
11. Busca por apelido não diferencia maiúsculas.
12. Os testes rodam contra a memória e contra o banco; `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Comprar ou trocar avatar, jogar partidas ou mudar qualquer dado pelo MCP.
- Login ou controle de acesso nos servidores: rodam na máquina de quem usa, sobre o banco local.
- Publicar os servidores na internet (no Render ou em outro lugar).
- Um servidor MCP para os adversários automáticos (spec 010), que ainda não estão na `main`.
