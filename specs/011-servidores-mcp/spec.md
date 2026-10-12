# Spec 011 — Servidores MCP: ranking, perfil e loja

**Branch:** `011-servidores-mcp` · **Status:** parte 1 (ranking) implementada; perfil e loja a seguir · **Criada em:** 12/10/2026 · **Dono:** Severino (banco de dados) · **Origem:** [SPEC/2026-10-12-servidores-mcp.md](../../SPEC/2026-10-12-servidores-mcp.md)

## Contexto
O professor pediu três servidores MCP (Model Context Protocol) para o aplicativo. Um MCP deixa um assistente de IA chamar ferramentas de um programa durante a conversa. Aqui, as ferramentas consultam os dados do CircuitCrash: ranking, perfil e loja, as três áreas com dados reais no banco desde as specs 002 e 006.

Os três servidores só leem. Comprar, trocar avatar ou gravar partida continua só no site, onde o servidor valida cada ação (constituição V).

Fora do escopo: qualquer escrita pelo MCP, login ou controle de acesso nos servidores, publicação na internet e um servidor para os adversários automáticos (spec 010, ainda fora da `main`).

## Histórias de usuário

### H1 — Ranking (prioridade P1)
Como jogador, quero perguntar ao assistente quem lidera o ranking e em que posição estou.

**Teste independente:** ligar o servidor de ranking ao Claude Code, perguntar "quem são os 5 primeiros do CircuitCrash?" e conferir com a tela `/ranking`.

Critérios de aceitação:
1. **Dado** o banco com os dados de exemplo, **quando** peço o ranking, **então** recebo os jogadores na mesma ordem da tela `/ranking`, com posição, apelido, rating, partidas e taxa de vitória.
2. Posso pedir só os primeiros N, de 1 a 50; o padrão é 10. Fora disso, o valor é ajustado ao limite mais próximo.
3. **Dado** um apelido, **quando** peço a posição, **então** recebo posição e rating; **dado** um jogador no período provisório, **então** a resposta diz que ele ainda não está no ranking e quantas partidas faltam.
4. **Dado** um apelido que não existe, **então** a resposta diz isso, sem erro.

### H2 — Perfil (P1)
Como jogador, quero perguntar ao assistente como estou indo, sem abrir o site.

**Teste independente:** perguntar "como está o perfil do voltz_br?" e conferir com `/perfil` como `voltz_br`.

Critérios de aceitação:
1. **Dado** um apelido, **quando** peço o perfil, **então** recebo rating, posição no ranking (ou "provisório"), Fagulhas, partidas, vitórias, taxa de vitória, objetivos capturados, avatar em uso, as 5 partidas mais recentes, as missões do dia e as conquistas, com os mesmos números da tela `/perfil`.
2. O e-mail do jogador nunca aparece.
3. **Dado** um apelido que não existe, **então** a resposta diz isso, sem erro.

### H3 — Loja (P2)
Como jogador, quero perguntar ao assistente o que posso comprar com as minhas Fagulhas.

**Teste independente:** perguntar "o que o luma_dev pode comprar?" e conferir com `/loja` como `luma_dev`.

Critérios de aceitação:
1. Posso listar os avatares com nome, raridade, preço e descrição, todos ou de uma raridade só; os exclusivos aparecem como "não vendido".
2. **Dado** um apelido, **quando** pergunto o que ele pode comprar, **então** recebo as Fagulhas dele, os avatares que já pode comprar e, para os outros à venda, quantas Fagulhas faltam, do mais barato para o mais caro.
3. Avatares que ele já tem e os exclusivos não aparecem como compráveis.
4. Raridade desconhecida ou apelido inexistente dão uma mensagem clara, sem erro.

## Requisitos funcionais
- **RF-01** Três servidores MCP independentes: `circuitcrash-ranking`, `circuitcrash-perfil` e `circuitcrash-loja`, cada um iniciado por um comando próprio.
- **RF-02** Os servidores falam com os dados só pelo contrato `Repositorio` (constituição IV), sem método novo nem alterado no contrato.
- **RF-03** Banco escolhido como no site: `DATABASE_URL` do `.env`; vazio, dados de exemplo em memória.
- **RF-04** Nenhuma ferramenta muda dados.
- **RF-05** Busca de jogador por apelido sem diferenciar maiúsculas e ignorando espaços nas pontas.
- **RF-06** O e-mail dos jogadores não sai em nenhuma resposta.
- **RF-07** Respostas estruturadas (campos com nome), para o assistente montar a frase.
- **RF-08** Funciona igual com os dados em memória e com o banco.

## Critérios de sucesso
- **CS-01** Os três servidores aparecem conectados no Claude Code com o arquivo de configuração do projeto, e cada ferramenta responde a uma pergunta de teste.
- **CS-02** Os números das respostas batem com as telas `/ranking`, `/perfil` e `/loja` para `voltz_br` e `luma_dev`.
- **CS-03** Os testes de cada ferramenta rodam contra a memória e contra o banco.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Entidades
Nenhuma nova. Usa Jogador, Avatar, Resumo da partida, Missão e Conquista das specs 001, 002 e 006.

## Pontos para a revisão (Henrique)
1. **Dependência nova:** o SDK oficial de MCP para Python.
2. **Nenhuma mudança no contrato `Repositorio`:** a busca por apelido usa `listar_jogadores`.
