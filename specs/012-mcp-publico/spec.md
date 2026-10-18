# Spec 012 — Servidor MCP público do CircuitCrash

**Branch:** `012-mcp-publico` · **Status:** em implementação · **Criada em:** 18/10/2026 · **Dono:** Severino · **Origem:** [SPEC/2026-10-18-mcp-publico.md](../../SPEC/2026-10-18-mcp-publico.md)

## Contexto
A spec 011 entregou o servidor MCP `circuitcrash` só por stdio: quem quer usá-lo precisa clonar o repositório e rodar `uv run circuitcrash-mcp`. Esta spec publica o mesmo servidor por Streamable HTTP, dentro do site que já roda no Render (spec 004), para pessoas de fora conectarem pelo endereço.

O MCP não tem login, então a dupla decidiu (18/10) que o servidor público **não grava** o resultado das partidas: só calcula e mostra. Como várias pessoas podem conectar ao mesmo tempo, a partida em andamento deixa de ser uma só no processo e passa a ser **uma por sessão MCP**.

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
1. **Dado** duas sessões MCP, **quando** cada uma inicia uma partida, **então** cada uma vê só a sua: jogar numa não muda a outra.
2. **Dado** uma sessão nova, **quando** chama `ver_partida`, **então** recebe "nenhuma partida em andamento", mesmo que outra sessão esteja jogando.
3. Uma sessão parada é descartada depois de um tempo, e o número de sessões ao mesmo tempo tem limite, para caber na memória do plano gratuito.

## Requisitos funcionais
- **RF-01** O site monta o servidor MCP em `/mcp` (Streamable HTTP, com sessão). O ciclo de vida do gerenciador de sessões do MCP roda junto com o do site.
- **RF-02** `criar_servidor` ganha a opção de não gravar. O site usa o servidor sem gravar; o comando `circuitcrash-mcp` (stdio) continua gravando.
- **RF-03** A partida em andamento fica numa `Mesa` por sessão MCP. No stdio há uma sessão só, então nada muda para quem usa localmente.
- **RF-04** O resultado da partida, gravado ou não, é calculado pela mesma `economia.resultado_da_demo`. A resposta ganha o campo `gravado`.
- **RF-05** O servidor público lê o mesmo repositório do site e não chama nenhum método de escrita dele.
- **RF-06** Sessões paradas por 10 minutos são descartadas; no máximo 100 sessões ao mesmo tempo.
- **RF-07** Nenhuma resposta traz e-mail (como na 011).

## Critérios de sucesso
- **CS-01** Depois do deploy, o Claude Code conecta pelo endereço público, lista as seis tools e consulta o ranking.
- **CS-02** Uma partida completa pelo endereço público termina com o resultado mostrado, e `/perfil` do jogador não muda.
- **CS-03** Testes: o site responde ao MCP em `/mcp` (listar tools e consultar o ranking por HTTP), duas sessões têm partidas separadas, o fim sem gravar não chama o repositório, e o stdio continua gravando.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Tríade letal no servidor público
- **Dados privados:** o servidor público não entrega e-mail nem dados de conta. Ranking e apelidos já são públicos no site.
- **Conteúdo não confiável:** o apelido de quem entra com Google é escolhido pela própria pessoa e chega ao agente nas respostas. Isso já acontecia na 011. Agora o servidor fica acessível a qualquer agente.
- **Comunicação externa:** o servidor continua sem acessar a rede. Para o agente, porém, ele agora fica do outro lado da internet. Como não grava nada, um agente enganado não consegue mudar dados por ele.

## Fora do escopo
- Login, token ou OAuth no MCP e gravar resultados pelo servidor público.
- Tools novas ou mudança no contrato `Repositorio`.
- Partidas que sobrevivem a reinícios do Render ou a mais de uma instância.

## Pontos para a revisão (Henrique)
1. **`app.py`:** ganha a rota `/mcp` e um `lifespan` que liga o gerenciador de sessões do MCP. As outras rotas não mudam.
2. **Sem proteção contra DNS rebinding no `/mcp`:** ela serve para servidores locais. O servidor público aceita qualquer `Host`, como o resto do site.
3. **Plano gratuito do Render:** o serviço dorme sem uso, então a primeira conexão pode demorar perto de um minuto.
