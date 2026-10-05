# Tarefas — 008 Login com a conta Google

**Entrada:** [spec.md](spec.md), [plan.md](plan.md). `[P]` = pode ser feita em paralelo. `[H#]` = história atendida.

## Fase 1 — Regras puras (H1, H2)
- [x] T001 [H1] [H2] `tests/test_conta.py`: `conferir_identidade` (boa, emissor, destinatário, validade, `nonce`, e-mail não confirmado, sem `sub`) e `sugerir_apelido` (acentos, símbolos, 20 caracteres, sem nome, repetidos)
- [x] T002 [H1] [H2] `domain/conta.py`: `ErroLogin`, `Identidade`, `conferir_identidade` e `sugerir_apelido`; T001 passa

## Fase 2 — Repositório (H1)
- [x] T003 [H1] `tests/test_login_repositorio.py` com a fixture `repo`: achar pelo `sub` e pelo e-mail, criar ligado, `vincular_google` uma vez só, `entrar_com_google` nos três caminhos e com e-mail ligado a outra conta; só banco: `sub` repetido recusado
- [x] T004 [H1] `dados/repositorio.py`: os quatro métodos no `Protocol`
- [x] T005 [H1] `dados/memoria.py` e `dados/sql.py`: os quatro métodos
- [x] T006 [H1] `domain/conta.py`: `entrar_com_google`; T003 passa

## Fase 3 — Rotas e tela (H1, H2, H3)
- [x] T007 [H1] [H2] [H3] `tests/test_login.py` com o Google falso: sem configuração, `/entrar`, retorno, segunda entrada, `state` errado, cancelamento, retorno repetido, `nonce` errado, **Sair**, **Demo como** restrito, `ler_id_token`
- [x] T008 [H1] [H2] `login/google.py`: `ConfigGoogle.do_ambiente()`, `nova_tentativa`, `url_de_autorizacao`, `trocar_codigo`, `ler_id_token`
- [x] T009 [H1] [H2] [H3] `app.py`: `/entrar`, `/auth/google/retorno`, `/sair`, `/jogador` restrito; `criar_app(repo, google_config=None, trocar_codigo=None)` (o nome `google` já é o do módulo); `perfil.html` também esconde os botões "Demo: ver como" para quem entrou com Google
- [x] T010 [H3] `web/templates/base.html` e `app.css`: **Entrar com Google** ou **Sair** no cabeçalho, a 360 px

## Fase 4 — Configuração e acabamento
- [x] T011 [P] `.env.example` e `render.yaml` (`sync: false` para as credenciais, `GOOGLE_REDIRECT_URI` fixo)
- [x] T012 [P] `README.md` (como criar o cliente OAuth) e status da spec
- [ ] T013 Conferir à mão com o cliente OAuth da dupla: entrar, comprar, sair, entrar de novo; se as credenciais não existirem até o congelamento, registrar aqui — pendente em 05/10: o cliente OAuth ainda não foi criado (`GOOGLE_CLIENT_ID` vazio no `.env`). Conferido no servidor local com um ID falso: o botão aparece, `/entrar` redireciona ao Google com `state`, `nonce` e `code_challenge`, e um retorno sem tentativa volta ao início sem erro
- [x] T014 `pytest`, `ruff check`, `ruff format --check` e `mypy` sem erros

## Dependências
Fase 1 → Fase 2 → Fase 3 → Fase 4. Em cada fase, os testes vêm antes da implementação. T009 depende de T006 e T008.
