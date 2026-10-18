# Spec 012 — Servidor MCP público do CircuitCrash

**Branch:** `012-mcp-publico` · **Status:** implementada, mesclada (PR #12) e conferida no Render em 18/10/2026 (T011) · **Criada em:** 18/10/2026 · **Dono:** Severino · **Origem:** [SPEC/2026-10-18-mcp-publico.md](../../SPEC/2026-10-18-mcp-publico.md)

## Contexto
A spec 011 entregou o servidor MCP `circuitcrash` só por stdio: quem quer usá-lo precisa clonar o repositório e rodar `uv run circuitcrash-mcp`. Esta spec publica o mesmo servidor por Streamable HTTP, dentro do site que já roda no Render (spec 004), para pessoas de fora conectarem pelo endereço.

O MCP não tem login, então a dupla decidiu (18/10) que o servidor público **não grava** o resultado das partidas: só calcula e mostra. Como várias pessoas podem conectar ao mesmo tempo, a partida em andamento deixa de ser uma só no processo e passa a ser identificada por um **`partida_id`**.

**Correção de 18/10 (antes do código do servidor):** a primeira versão desta spec guardava uma partida por sessão MCP. O SDK `mcp` 2.3 fala a revisão 2026-07-28 do protocolo, em que cada pedido chega numa conexão nova, sem sessão (conferido: `ctx.session` e a conexão mudam a cada chamada de tool, mesmo com o mesmo cliente). Por isso o estado da partida vai explícito: `iniciar_partida` devolve um `partida_id`, e as outras tools da partida o recebem.

## Histórias de usuário

### H1 — Conectar sem instalar (prioridade P1)
Como pessoa de fora da dupla, quero ligar meu agente ao CircuitCrash só com o endereço público.

**Teste independente:** `claude mcp add --transport http circuitcrash https://circuitcrash.onrender.com/mcp`, depois `/mcp` mostra o servidor conectado com seis tools, e "quem lidera o ranking do CircuitCrash?" responde com o mesmo topo da tela `/ranking`.

Critérios de aceitação:
1. **Dado** o site no ar, **quando** um cliente MCP conecta em `/mcp`, **então** recebe as instruções do servidor e as seis tools da spec 011, com as mesmas anotações de leitura e escrita.
2. **Dado** o servidor público, **quando** consulto o ranking ou a posição de um jogador, **então** recebo os mesmos números da tela `/ranking`.
3. As rotas do site e `/health` continuam iguais.

### H2 — Jogar sem mexer no ranking (P1)
Como pessoa de fora, quero jogar a partida de demonstração pelo agente e ver o resultado, sem mudar os dados dos jogadores.

Critérios de aceitação:
1. **Dado** o servidor público, **quando** inicio, consulto, jogo e passo, **então** valem as mesmas regras e respostas da spec 011.
2. **Dado** o fim da partida, **então** a resposta traz colocação, pontos, objetivos, Fagulhas e rating antes e depois, com `gravado: false`, e a mensagem diz que o servidor público não grava. O repositório não recebe a partida.
3. As instruções do servidor público e a docstring de `iniciar_partida` dizem que o resultado não é gravado.

### H3 — Uma partida por pessoa (P1)
Como pessoa de fora, quero que a minha partida não seja atrapalhada por outra pessoa conectada ao mesmo tempo.

Critérios de aceitação:
1. **Dado** o servidor público, **quando** inicio uma partida, **então** a resposta traz um `partida_id` aleatório, difícil de adivinhar, e as instruções dizem para passá-lo em `ver_partida`, `jogar_peca` e `passar_vez`.
2. **Dado** duas partidas iniciadas, **quando** jogo numa pelo seu `partida_id`, **então** a outra não muda.
3. **Dado** o servidor público, **quando** chamo uma tool da partida sem `partida_id` ou com um id desconhecido (expirado, de antes de um reinício ou inventado), **então** recebo mensagem clara mandando usar `iniciar_partida`, sem erro.
4. **Dado** o servidor local (stdio), **quando** não passo `partida_id`, **então** vale a última partida iniciada, e o uso da spec 011 continua igual.
5. Uma partida parada é descartada depois de um tempo, e o número de partidas guardadas tem limite, para caber na memória do plano gratuito.

## Requisitos funcionais
- **RF-01** O site monta o servidor MCP em `/mcp` (Streamable HTTP sem sessão, `stateless_http`). O ciclo de vida do gerenciador do MCP roda junto com o do site.
- **RF-02** `criar_servidor` ganha o modo público: não grava e exige `partida_id`. O site usa o modo público; o comando `circuitcrash-mcp` (stdio) continua no modo local, gravando.
- **RF-03** Cada partida fica numa `Mesa` guardada por `partida_id` (gerado com `secrets`). `ver_partida`, `jogar_peca` e `passar_vez` ganham o parâmetro `partida_id`, opcional no modo local. As respostas da partida ganham o campo `partida_id`.
- **RF-04** O resultado da partida, gravado ou não, é calculado pela mesma `economia.resultado_da_demo`. A resposta ganha o campo `gravado`.
- **RF-05** O servidor público lê o mesmo repositório do site e não chama nenhum método de escrita dele.
- **RF-06** Partidas paradas por 30 minutos são descartadas; no máximo 200 guardadas (a mais antiga sem uso sai primeiro).
- **RF-07** Nenhuma resposta traz e-mail (como na 011).

## Critérios de sucesso
- **CS-01** Depois do deploy, o Claude Code conecta pelo endereço público, lista as seis tools e consulta o ranking.
- **CS-02** Uma partida completa pelo endereço público termina com o resultado mostrado, e `/perfil` do jogador não muda.
- **CS-03** Testes: o site responde ao MCP em `/mcp` (listar tools e consultar o ranking por HTTP), duas partidas com ids diferentes ficam separadas, id ausente ou desconhecido responde sem erro, partidas velhas expiram, o fim sem gravar não chama o repositório, e o stdio continua gravando.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Tríade letal no servidor público
- **Dados privados:** o servidor público não entrega e-mail nem dados de conta. Ranking e apelidos já são públicos no site.
- **Conteúdo não confiável:** o apelido de quem entra com Google é escolhido pela própria pessoa e chega ao agente nas respostas. Isso já acontecia na 011. Agora o servidor fica acessível a qualquer agente.
- **Comunicação externa:** o servidor continua sem acessar a rede. Para o agente, porém, ele agora fica do outro lado da internet. Como não grava nada, um agente enganado não consegue mudar dados por ele.

## Fora do escopo
- Login, token ou OAuth no MCP e gravar resultados pelo servidor público.
- Tools novas ou mudança no contrato `Repositorio`.
- Sessão MCP (cabeçalho `Mcp-Session-Id`): a revisão do protocolo usada pelo SDK não tem sessão.
- Partidas que sobrevivem a reinícios do Render ou a mais de uma instância.

## Pontos para a revisão (Henrique)
1. **`app.py`:** ganha a rota `/mcp` e um `lifespan` que liga o gerenciador do MCP. As outras rotas não mudam.
2. **`partida_id` nas tools da partida:** muda a assinatura das tools de 011, mas o parâmetro é opcional no modo local, então os pedidos antigos continuam valendo.
3. **Sem proteção contra DNS rebinding no `/mcp`:** ela serve para servidores locais. O servidor público aceita qualquer `Host`, como o resto do site.
4. **Plano gratuito do Render:** o serviço dorme sem uso, então a primeira conexão pode demorar perto de um minuto.
