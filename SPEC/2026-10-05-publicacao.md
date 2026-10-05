# Publicação

**Data:** 05/10/2026 · **Status:** proposta, sem código ainda · **Branch:** `003-entrega`

## O quê
Publicar o CircuitCrash num endereço público com HTTPS, no Render, como Web Service no plano gratuito, a partir da branch `main` deste repositório. A cada início do serviço, a carga de exemplo roda com `--recriar` antes do servidor subir, para que qualquer pessoa que abra o link encontre a demonstração no estado inicial, com as missões do dia na data certa.

## Por quê
A entrega e a apresentação de 06/10 precisam de um link que a turma e o professor abram no computador ou no celular, sem instalar nada e sem depender do notebook da dupla. O plano gratuito basta para uma demonstração. Rodar `--recriar` ao iniciar resolve dois limites do plano gratuito de uma vez: o disco do serviço é apagado a cada reinício, e o serviço dorme quando fica sem acesso. Com a carga no início, o banco sempre existe e começa igual.

## Critérios de aceitação
1. **Dado** o serviço publicado, **quando** abro a URL pública no navegador do computador ou do celular, **então** a página inicial abre por HTTPS, sem erro.
2. **Dado** o serviço publicado, **então** todas as telas da interface web (início, partida, perfil, loja, ranking e regras) abrem sem erro e com o mesmo conteúdo da execução local com banco.
3. **Dado** que o serviço inicia (primeiro deploy, novo deploy ou volta depois de dormir), **então** a carga roda com `--recriar` antes do servidor aceitar acessos, e o primeiro acesso já vê os jogadores, avatares e missões de exemplo.
4. **Dado** que a carga falha ao iniciar, **então** o servidor não sobe e o erro aparece no log do Render.
5. **Dado** o serviço no ar, **quando** troco Fagulhas por um avatar, **então** a troca aparece no perfil enquanto o serviço continuar no ar.
6. O servidor escuta em `0.0.0.0`, na porta que o Render informa, sem recarga automática de código.
7. A `SECRET_KEY` e a `DATABASE_URL` ficam só nas variáveis de ambiente do Render. Nenhum segredo entra no repositório.
8. Um push na `main` publica a versão nova sem passo manual.
9. A URL pública está no README.
10. Alguém da dupla consegue refazer a publicação do zero seguindo só o README, em menos de 15 minutos.
11. `pytest`, `ruff` e `mypy` continuam passando, e o jeito de rodar localmente não muda.

## Fora do escopo
- Plano pago, domínio próprio e mais de uma instância.
- Banco que guarde os dados entre reinícios (PostgreSQL gerenciado ou disco persistente). No plano gratuito, compras e trocas de avatar voltam ao estado inicial a cada reinício, e isso é aceito para a demonstração.
- Evitar que o serviço durma ou acelerar o primeiro acesso depois de dormir.
- Login Google.
- Monitoramento, alertas e backup.
- Integração contínua que rode os testes antes do deploy.
