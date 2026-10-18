# Servidor MCP público do CircuitCrash

**Data:** 18/10/2026 · **Status:** implementada em 18/10/2026, aguardando revisão e a conferência no Render · **Branch:** `012-mcp-publico` · **Detalhes:** `specs/012-mcp-publico/`

## O quê
O servidor MCP `circuitcrash` (spec 011) passa a ser publicado também na internet, junto do site no Render, em `https://circuitcrash.onrender.com/mcp` (transporte Streamable HTTP). Qualquer pessoa liga o próprio agente a ele sem clonar o repositório, por exemplo no Claude Code:

```bash
claude mcp add --transport http circuitcrash https://circuitcrash.onrender.com/mcp
```

No servidor público:

- As três consultas (`ver_ranking`, `posicao_do_jogador`, `ver_partida`) funcionam como no servidor local.
- A partida de demonstração também funciona: `iniciar_partida` devolve um **`partida_id`**, que o agente passa nas jogadas seguintes. Quem conecta não mexe na partida de outra pessoa.
- No fim da partida, o resultado (colocação, Fagulhas e rating) é **calculado e mostrado, mas não gravado**. Sem login no MCP, gravar deixaria qualquer pessoa mudar o rating de qualquer jogador.

O servidor local por stdio (`uv run circuitcrash-mcp`) continua como estava: uma partida e o resultado gravado no banco.

## Por quê
O exercício da spec 011 terminou com o servidor rodando só na máquina de quem clona o projeto. Publicar deixa a professora, os colegas e qualquer agente compatível com MCP usarem a aplicação pelo endereço público, sem instalar nada, e sem abrir o ranking para escrita anônima.

## Critérios de aceitação
1. **Dado** o site publicado, **quando** um cliente MCP conecta em `/mcp`, **então** ele lista as mesmas seis tools do servidor local.
2. **Dado** o servidor público, **quando** peço o ranking ou a posição de um jogador, **então** recebo os mesmos números da tela `/ranking`.
3. **Dado** duas partidas iniciadas, **quando** jogo numa pelo seu `partida_id`, **então** a outra não muda; sem id ou com id desconhecido, a resposta manda iniciar uma partida.
4. **Dado** o fim de uma partida no servidor público, **então** a resposta traz colocação, pontos, Fagulhas e rating antes e depois, marcada como não gravada, e o banco não muda.
5. **Dado** o servidor local por stdio, **então** tudo continua como na spec 011 (resultado gravado).
6. O site continua respondendo como antes, e `/health` não depende do MCP.
7. O README explica como conectar ao servidor público.
8. Testes; `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Login ou token no MCP e gravar resultados pelo servidor público.
- Tools novas.
- Guardar a partida entre reinícios do Render: ela fica na memória, e uma partida parada some depois de 30 minutos.

A primeira versão desta spec, do mesmo dia, guardava uma partida por sessão MCP. Foi corrigida antes do código do servidor: o SDK `mcp` 2.3 usa a revisão 2026-07-28 do protocolo, que não tem sessão.
