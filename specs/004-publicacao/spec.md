# Spec 004 — Publicação

**Branch:** `004-publicacao` · **Status:** em implementação · **Criada em:** 05/10/2026 · **Origem:** [SPEC/2026-10-05-publicacao.md](../../SPEC/2026-10-05-publicacao.md)

## Contexto
A entrega e a apresentação de 06/10 precisam de um link que a turma e o professor abram no computador ou no celular, sem instalar nada e sem depender do notebook da dupla. Esta spec publica o CircuitCrash num endereço público com HTTPS, no plano gratuito de um serviço de hospedagem, a partir da branch `main`.

No plano gratuito o disco é apagado a cada reinício e o serviço dorme quando fica sem acesso. Por isso, a cada início, a carga de exemplo roda com `--recriar` antes do servidor subir: o banco sempre existe e começa igual, com as missões do dia na data certa.

Fora do escopo: plano pago, domínio próprio e mais de uma instância; banco que guarde os dados entre reinícios; evitar que o serviço durma; login Google; monitoramento, alertas e backup; integração contínua que rode os testes antes do deploy.

## Histórias de usuário

### H1 — Abrir a demonstração por um link (prioridade P1)
Como pessoa da turma ou professor, quero abrir o CircuitCrash por um link, no computador ou no celular, sem instalar nada.

**Teste independente:** abrir a URL pública num navegador de celular e navegar por todas as telas.

Critérios de aceitação:
1. **Dado** o serviço publicado, **quando** abro a URL pública, **então** a página inicial abre por HTTPS, sem erro.
2. **Dado** o serviço publicado, **então** início, partida, perfil, loja, ranking e regras abrem sem erro e com o mesmo conteúdo da execução local com banco.
3. **Dado** o serviço no ar, **quando** troco Fagulhas por um avatar, **então** a troca aparece no perfil enquanto o serviço continuar no ar.

### H2 — A demonstração sempre começa igual (P1)
Como apresentador, quero que todo início do serviço comece com os dados de exemplo.

Critérios de aceitação:
1. **Dado** que o serviço inicia (primeiro deploy, novo deploy ou volta depois de dormir), **então** a carga roda com `--recriar` antes do servidor aceitar acessos, e o primeiro acesso já vê os jogadores, avatares e missões de exemplo.
2. **Dado** que a carga falha ao iniciar, **então** o servidor não sobe e o erro aparece no log do serviço.

### H3 — Publicar sem passo manual e sem segredos no repositório (P1)
Como dupla, quero que um push na `main` publique a versão nova e que nenhum segredo fique no Git.

Critérios de aceitação:
1. O servidor escuta em `0.0.0.0`, na porta que o serviço informa, sem recarga automática de código.
2. A `SECRET_KEY` e a `DATABASE_URL` ficam só nas variáveis de ambiente do serviço. Nenhum segredo entra no repositório.
3. Um push na `main` publica a versão nova sem passo manual.
4. A URL pública está no README.
5. Alguém da dupla consegue refazer a publicação do zero seguindo só o README, em menos de 15 minutos.
6. `pytest`, `ruff` e `mypy` continuam passando, e o jeito de rodar localmente não muda.
