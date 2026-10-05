# Banco de dados

**Data:** 04/10/2026 · **Status:** implementada · **Origem:** `specs/002-banco-de-dados/` (spec, plan e tasks completos)

## O quê
Guardar em banco de dados os jogadores, avatares, inventários, partidas recentes, missões e conquistas, sem mudar nenhuma tela nem nenhuma regra. Por padrão o banco é um arquivo SQLite; um servidor PostgreSQL é opcional. Com a configuração do banco vazia, o sistema continua com os dados em memória. Uma carga de exemplo enche o banco com os mesmos dados da interface web, e a opção `--recriar` apaga tudo e carrega de novo.

## Por quê
Na interface web, toda compra ou troca de avatar sumia quando o servidor reiniciava. A demonstração de 06/10 precisa mostrar que o progresso do jogador fica salvo. A prioridade é algo simples e funcionando: um banco em arquivo, que não exige instalar nada.

## Critérios de aceitação

### O progresso do jogador não se perde
1. **Dado** o banco configurado, **quando** troco Fagulhas por um avatar e o servidor reinicia, **então** o avatar continua no inventário e as Fagulhas continuam descontadas.
2. **Dado** o banco configurado, **quando** passo a usar outro avatar e o servidor reinicia, **então** o perfil e o cabeçalho mostram o avatar escolhido.
3. As Fagulhas de um jogador nunca ficam negativas, mesmo que alguém tente gravar um valor errado direto no banco.

### A demonstração continua igual
4. **Dado** um banco vazio, **quando** rodo a carga de exemplo, **então** todas as telas mostram o mesmo conteúdo que mostravam com os dados em memória, na mesma ordem.
5. **Dado** um banco que já tem dados, **quando** rodo a carga de novo, **então** nada é duplicado.
6. Um único comando (`--recriar`) apaga tudo e recarrega os dados de exemplo.

### Funciona com ou sem banco
7. Configuração do banco vazia: o sistema usa os dados em memória.
8. Endereço de banco em arquivo: o sistema usa esse arquivo. Endereço de servidor: usa esse servidor.
9. Os testes da loja e do ranking passam contra os dados em memória e contra o banco.
10. O contrato `Repositorio` não muda: telas e regras usam os mesmos métodos.

### Estrutura e segurança
11. A estrutura do banco é criada e atualizada só por migrações versionadas.
12. Apelido, e-mail e identificador Google são únicos entre os jogadores. O identificador Google fica vazio por enquanto e nenhuma senha é guardada.
13. O endereço e a senha do banco ficam só no `.env`.
14. Alguém da dupla cria o banco e carrega o exemplo seguindo só o README, em menos de 5 minutos.
15. `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Login Google (só fica o espaço para o identificador da conta).
- Gravar as partidas jogadas na tela `/partida`.
- Aplicar Fagulhas e rating ao fim da partida.
- Compra atômica no contrato `Repositorio` (fica para uma próxima spec, com o aceite dos dois).
- Missões com progresso real por dia (o progresso de exemplo vale só para o dia da carga).
- Campeonatos, painel de administração e hospedagem.
