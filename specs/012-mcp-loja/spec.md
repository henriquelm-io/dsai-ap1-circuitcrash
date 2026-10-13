# Spec 012 — Loja de avatares no servidor MCP

**Branch:** `012-mcp-loja` · **Status:** aprovada e implementada em 13/10/2026 · **Criada em:** 13/10/2026 · **Dono:** Henrique · **Origem:** [SPEC/2026-10-13-mcp-loja.md](../../SPEC/2026-10-13-mcp-loja.md)

## Contexto
A spec 011 criou o servidor MCP `circuitcrash`, com o ranking e a partida de demonstração, e deixou a loja fora do escopo. Esta spec acrescenta ao **mesmo** servidor uma consulta da loja de avatares, só de leitura. Comprar e equipar continuam só pelo site, onde o jogador está logado.

## Histórias de usuário

### H1 — Consultar a loja de um jogador (prioridade P1)
Como jogador, quero perguntar ao agente quantas Fagulhas tenho, quais avatares já são meus e o que consigo comprar agora.

**Teste independente:** pedir ao agente "o que o lia.ohm consegue comprar na loja?" e comparar a resposta com a tela `/loja` aberta como `lia.ohm`.

Critérios de aceitação:
1. **Dado** um apelido, **quando** consulto a loja, **então** recebo:
   - as Fagulhas do jogador;
   - o avatar equipado (ou nenhum);
   - os avatares que ele possui;
   - o catálogo inteiro, na ordem da tela `/loja`, com nome, raridade, preço e situação de cada avatar.
2. A situação de cada avatar é a mesma da tela `/loja`, nesta ordem de prioridade:
   1. **em uso**: é o avatar equipado;
   2. **possui**: está no inventário;
   3. **exclusivo**: não é vendável;
   4. **pode comprar**: o preço cabe no saldo;
   5. **faltam Fagulhas**: o preço não cabe.
3. **Dado** um jogador com saldo suficiente, **então** cada avatar vendável que ele não possui e cujo preço é menor ou igual ao saldo vem marcado como comprável.
4. **Dado** um jogador sem saldo para nenhum avatar, **então** nenhum vem como comprável, e cada avatar vendável diz quantas Fagulhas faltam.
5. **Dado** um jogador novato, sem avatar e sem inventário, **então** o avatar equipado vem vazio, a lista dos que ele possui vem vazia, e o catálogo vem completo.
6. Um avatar exclusivo vem como não vendável, sem preço e nunca comprável, mesmo para quem tem saldo para tudo. Se o jogador já o possui, aparece como possuído e continua não vendável.
7. Apelido sem diferenciar maiúsculas. **Dado** um apelido inexistente, **então** a resposta diz que não há jogador com esse apelido, sem erro e sem catálogo.

### H2 — Leitura liberada, sem mudar nada (P1)
Como dupla, queremos que o agente consulte a loja sem pedir licença e sem nenhum risco de gastar Fagulhas.

Critérios de aceitação:
1. A tool está em `allow` nas permissões do projeto e é anotada como leitura.
2. Depois da consulta, Fagulhas, inventário e avatar equipado do jogador continuam iguais.
3. A docstring diz quando usar a tool e avisa que ela não compra nem equipa.

## Requisitos funcionais
- **RF-01** Uma tool nova, `consultar_loja(apelido)`, registrada no servidor `circuitcrash` da spec 011. Nenhum servidor novo.
- **RF-02** Somente leitura: a tool não compra, não equipa e não grava nada.
- **RF-03** Preço, raridade e exclusividade vêm de `domain/modelos.py` (`Avatar.preco`, `Raridade`, `PRECOS`). A situação de cada avatar é calculada por uma única regra em `domain/loja.py`, usada pela tela `/loja` e pelo MCP. Nenhuma regra de preço ou de situação é duplicada.
- **RF-04** Os dados vêm do contrato `Repositorio`, sem método novo ou alterado. O banco é escolhido como no site: `DATABASE_URL` do `.env`; sem ela, os dados de exemplo em memória.
- **RF-05** O e-mail dos jogadores não sai em nenhuma resposta.
- **RF-06** Resposta estruturada, com campos nomeados, e uma mensagem curta em texto.

## Critérios de sucesso
- **CS-01** Para cada jogador dos dados de exemplo, a situação de cada avatar na resposta é a mesma da tela `/loja`.
- **CS-02** No Claude Code, o agente responde "o que eu consigo comprar?" usando só a tool, sem pedir licença.
- **CS-03** Testes da tool contra a memória e o banco, e pelo cliente MCP em processo.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Comprar ou equipar avatar pelo MCP.
- Filtro por raridade na tool.
- Perfil completo pelo MCP (missões, conquistas, histórico de partidas).
- Mudanças no contrato `Repositorio`, no banco ou nas migrações.

## Pontos para a revisão (Severino)
1. **Regra de situação no domínio:** a escolha entre em uso, possui, exclusivo, pode comprar e faltam sai de `app.pagina_loja` para `domain/loja.py`. O site e o MCP passam a usar a mesma função, e o comportamento da tela não muda.
2. **Nenhuma mudança no contrato `Repositorio`** nem dependência nova.
3. **Mais uma tool no servidor da spec 011:** passam a ser sete, quatro de leitura e três de escrita. `.claude/settings.json` ganha `mcp__circuitcrash__consultar_loja` em `allow`.
