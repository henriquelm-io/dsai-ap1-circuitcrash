# Spec 008 — Login com a conta Google

**Branch:** `008-login-google` · **Status:** implementada, aguardando revisão no PR · **Criada em:** 05/10/2026 · **Dono:** Severino · **Origem:** [SPEC/2026-10-05-login-google.md](../../SPEC/2026-10-05-login-google.md)

## Contexto
A spec 001 entregou as telas sem login, com o seletor **Demo como** para alternar entre dois perfis de exemplo. A spec 002 deixou no cadastro de jogadores o espaço para o identificador da conta Google (`google_sub`, único e vazio), e todas as specs até aqui puseram o login fora do escopo. Esta spec liga o login com a conta Google, para cada pessoa ter o próprio perfil.

O Google cuida da senha e confirma o e-mail. O CircuitCrash só recebe um identificador estável da conta, o nome e o e-mail.

Fora do escopo: outros provedores, trocar o apelido, apagar a conta, guardar as contas da versão publicada entre reinícios e painel de administração.

## Histórias de usuário

### H1 — Entrar com a minha conta Google (prioridade P1)
Como pessoa da turma, quero entrar com a minha conta Google e ter o meu próprio perfil, sem criar senha.

**Teste independente:** clicar em **Entrar com Google**, autorizar e ver o meu nome no perfil, com 0 Fagulhas e sem avatar.

Critérios de aceitação:
1. **Dado** o login configurado, **quando** autorizo na tela do Google, **então** volto ao CircuitCrash como o meu jogador.
2. **Dado** que é a primeira vez, **então** é criado um jogador com o meu nome do Google como apelido (sem repetir o de outro jogador), o meu e-mail, 0 Fagulhas, rating 1200 e sem avatar.
3. **Dado** que já entrei antes, **então** volto ao mesmo jogador, com tudo o que eu tinha.
4. **Dado** um jogador com o meu e-mail e sem conta Google ligada, **então** a minha conta é ligada a ele.
5. Só entra quem tem o e-mail confirmado pelo Google.

### H2 — Ninguém entra no meu perfil (P1)
Como jogador, quero que só eu use o meu perfil.

Critérios de aceitação:
1. O retorno do Google só é aceito se pertencer à tentativa de login começada neste navegador.
2. A resposta do Google só é aceita se foi emitida pelo Google, para o CircuitCrash, dentro da validade e para esta tentativa.
3. Cancelar ou dar erro no Google volta ao início com um aviso, sem entrar.
4. O seletor **Demo como** só troca para os perfis de demonstração.
5. Nenhuma senha é guardada; o identificador e a chave do login ficam fora do repositório.

### H3 — Sair, e a demonstração continua (P1)
Como apresentador, quero que a demonstração funcione sem login e que dê para sair.

Critérios de aceitação:
1. **Quando** clico em **Sair**, **então** volto ao perfil de demonstração padrão.
2. Sem o login configurado, o botão **Entrar com Google** não aparece e o resto funciona como antes.
3. As telas funcionam a partir de 360 px e sem HTMX.

## Requisitos funcionais
- **RF-01** O login usa o fluxo de autorização do Google com OpenID Connect, pedindo só nome, e-mail e identificador da conta.
- **RF-02** Cada tentativa de login tem um código aleatório de estado e um de uso único, guardados na sessão do navegador e conferidos no retorno; o código de troca é protegido por PKCE.
- **RF-03** A identidade só vale se o emissor for o Google, o destinatário for o CircuitCrash, estiver dentro da validade, o código de uso único bater e o e-mail estiver confirmado.
- **RF-04** O jogador é procurado primeiro pelo identificador Google e depois pelo e-mail; se não existir, é criado.
- **RF-05** O apelido novo vem do nome do Google (ou do começo do e-mail), só com letras, números, ponto, hífen e sublinhado, até 20 caracteres, e ganha um número no fim se já existir.
- **RF-06** Um e-mail já ligado a outra conta Google não é religado; a pessoa vê um aviso.
- **RF-07** O identificador e a chave do cliente Google vêm só de variáveis de ambiente.
- **RF-08** O seletor **Demo como** aceita só os perfis de demonstração.

## Critérios de sucesso
- **CS-01** Uma pessoa da dupla entra com a própria conta Google no servidor local e na versão publicada.
- **CS-02** Os testes cobrem o primeiro login, o retorno, a ligação por e-mail, o estado errado, o cancelamento, a identidade inválida (emissor, destinatário, validade, código de uso único, e-mail não confirmado) e o sair, sem acessar o Google de verdade.
- **CS-03** Os testes de repositório rodam contra a memória e o banco.
- **CS-04** `pytest`, `ruff` e `mypy` passam.

## Entidades
- **Identidade Google:** identificador estável da conta, e-mail, e-mail confirmado e nome.
- Usa o Jogador da spec 002, com o identificador Google já previsto na tabela.

## Pontos para a revisão (precisam do aceite do Henrique)
1. **Contrato `Repositorio`:** ganha métodos para procurar o jogador pelo identificador Google e pelo e-mail, criar um jogador já ligado a uma conta Google e ligar uma conta a um jogador existente.
2. **Credenciais:** o cliente OAuth é criado pela dupla no Google Cloud Console, com os endereços de retorno local e publicado, e a tela de consentimento em modo de teste com os e-mails da dupla e de quem for testar.
3. **Versão publicada:** como o banco volta ao exemplo a cada reinício, quem entrar com Google no Render perde o perfil quando o serviço dorme. É aceito para a demonstração.
4. **Conflito com as specs 006 e 007:** esta spec mexe no cabeçalho (`base.html`) e nas rotas de `app.py`, mas não na partida.
