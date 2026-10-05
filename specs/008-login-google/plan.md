# Plano — 008 Login com a conta Google

**Spec:** [spec.md](spec.md) · **Data:** 05/10/2026

## Resumo
Fluxo de autorização do OpenID Connect do Google, com `state`, `nonce` e PKCE, escrito com a biblioteca padrão do Python (`urllib`, `secrets`, `hashlib`, `base64`, `json`): nenhuma dependência nova. A conferência da identidade e a escolha do apelido ficam em `domain/conta.py`, em Python puro. A conversa com o Google fica em `circuitcrash/login/google.py`, que os testes trocam por uma versão falsa. O contrato `Repositorio` ganha quatro métodos para achar, criar e ligar jogadores pela conta Google. Não há tabela nova: `jogadores.google_sub` existe desde a migração `0001`.

## Contexto técnico
| Item | Escolha |
| --- | --- |
| Protocolo | OAuth 2.0 + OpenID Connect, fluxo de código de autorização com PKCE (S256), escopo `openid email profile` |
| HTTP com o Google | `urllib.request` (troca do código no endpoint de token), só no servidor |
| `id_token` | Recebido direto do endpoint de token do Google, por HTTPS, numa chamada feita pelo servidor; por isso a assinatura não precisa ser conferida (OpenID Connect Core, seção 3.1.3.7, item 6). Emissor, destinatário, validade e `nonce` são conferidos |
| Sessão | O `SessionMiddleware` que já existe (cookie assinado com `SECRET_KEY`) |
| Configuração | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e, opcional, `GOOGLE_REDIRECT_URI` |
| Testes | `trocar_codigo` falso injetado em `criar_app`; nenhum teste acessa o Google |

## Checagem da constituição
- I Python: ok, só a biblioteca padrão.
- II Spec antes de código: a spec foi commitada antes; este plano e as tarefas também.
- III Regras isoladas: `domain/conta.py` recebe as informações da identidade e o horário atual como parâmetros; não acessa rede nem relógio.
- IV Contrato de dados: quatro métodos novos, nenhum alterado. Precisa do aceite do Henrique.
- V Servidor decide: a identidade só vale depois de conferida no servidor; o navegador nunca escolhe o jogador da conta Google.
- VI Celular: o botão e o **Sair** cabem no cabeçalho a 360 px; são um link e um formulário, sem HTMX.
- VII Qualidade: testes para cada critério; o `.env` com as credenciais continua fora do Git.

## Estrutura
```text
src/circuitcrash/
├── domain/conta.py          # novo: Identidade, conferir_identidade(), sugerir_apelido(), entrar_com_google()
├── login/
│   ├── __init__.py
│   └── google.py            # novo: ConfigGoogle, nova_tentativa(), url_de_autorizacao(), trocar_codigo(), ler_id_token()
├── dados/
│   ├── repositorio.py       # + obter_jogador_por_google, obter_jogador_por_email, criar_jogador_google, vincular_google
│   ├── memoria.py           # implementa os quatro
│   └── sql.py               # implementa os quatro
├── app.py                   # /entrar, /auth/google/retorno, /sair; /jogador só aceita perfis de demonstração
└── web/templates/base.html  # Entrar com Google / Sair no cabeçalho
tests/
├── test_conta.py            # novo: regras puras
├── test_login_repositorio.py  # novo: fixture repo (memória e banco)
└── test_login.py            # novo: rotas com o Google falso
```

## Fluxo
1. `GET /entrar`: sem `GOOGLE_CLIENT_ID`, volta ao início com aviso. Com ele, `nova_tentativa()` gera `state`, `nonce` e o verificador PKCE, guarda os três na sessão e redireciona para `https://accounts.google.com/o/oauth2/v2/auth` com `client_id`, `redirect_uri`, `response_type=code`, `scope=openid email profile`, `state`, `nonce`, `code_challenge` (S256) e `prompt=select_account`.
2. `GET /auth/google/retorno`: tira a tentativa da sessão (vale uma vez só). Se vier `error`, se faltar `code` ou se o `state` não bater, volta ao início com aviso.
3. `trocar_codigo(config, code, verificador)`: `POST https://oauth2.googleapis.com/token` com `grant_type=authorization_code`, `code`, `redirect_uri`, `client_id`, `client_secret` e `code_verifier`; devolve as informações do `id_token` (a parte do meio, em base64url). Falha de rede ou resposta sem `id_token` levanta `ErroLogin`.
4. `conta.conferir_identidade(info, client_id, nonce, agora)`: `iss` em `accounts.google.com` ou `https://accounts.google.com`; `aud` igual ao `client_id`; `exp` maior que `agora`; `nonce` igual; `email_verified` verdadeiro; `sub` e `email` presentes. Devolve `Identidade` ou levanta `ErroLogin` com a mensagem do aviso.
5. `conta.entrar_com_google(repo, identidade, hoje)`: pelo `sub` → esse jogador; senão, pelo e-mail → liga a conta (`vincular_google`), a não ser que o e-mail já esteja ligado a outra conta; senão, cria com `sugerir_apelido` e id `g-<12 primeiros hex do sha256 do sub>`.
6. A sessão fica com `jogador_id` e `conta_google = True`, e o navegador vai para `/perfil` com o aviso "Olá, <apelido>!".
7. `POST /sair`: limpa `jogador_id`, `conta_google` e a partida em andamento, e volta ao início.
8. `POST /jogador` (Demo como): só aceita os ids de `listar_jogadores()[:2]` e encerra a sessão Google.

O endereço de retorno é `GOOGLE_REDIRECT_URI` quando definido, senão o da própria requisição (`/auth/google/retorno`). No Render ele vai fixo no `render.yaml`, porque o servidor atrás do proxy enxerga `http`.

## Apelido (`sugerir_apelido`)
Nome do Google, ou a parte do e-mail antes do `@` se o nome vier vazio; sem acentos (`unicodedata`), espaços viram `_`, só `[a-z0-9._-]`, em minúsculas, até 20 caracteres; vazio vira `jogador`. Se já existir (sem diferenciar maiúsculas), tenta `nome2`, `nome3`… cortando para caber nos 20.

## Contrato (`dados/repositorio.py`)
```python
def obter_jogador_por_google(self, google_sub: str) -> Jogador | None: ...


def obter_jogador_por_email(self, email: str) -> Jogador | None: ...


def criar_jogador_google(self, jogador: Jogador, google_sub: str) -> None:
    """Insere o jogador já ligado à conta Google."""


def vincular_google(self, jogador_id: str, google_sub: str) -> bool:
    """Liga a conta a um jogador sem conta; False se ele já tem outra."""
```
- Memória: um dicionário `google_sub → jogador_id`; o e-mail é comparado sem diferenciar maiúsculas.
- Banco: consultas em `jogadores.google_sub` e `lower(email)`; `criar_jogador_google` insere com a próxima `ordem` numa transação; `vincular_google` só atualiza se `google_sub` estiver vazio.

## Configuração
- `.env.example`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e o comentário de `GOOGLE_REDIRECT_URI`.
- `render.yaml`: `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` com `sync: false` (o valor é digitado no painel do Render e não entra no repositório) e `GOOGLE_REDIRECT_URI=https://circuitcrash.onrender.com/auth/google/retorno`.
- README: passo a passo do Google Cloud Console (cliente OAuth "Aplicativo da Web", endereços de retorno local e publicado, tela de consentimento em modo de teste).

## Testes
- `tests/test_conta.py`: `conferir_identidade` aceita a identidade boa e recusa emissor, destinatário, validade, `nonce`, e-mail não confirmado e falta de `sub`; `sugerir_apelido` limpa acentos e símbolos, corta em 20, usa o e-mail sem nome e numera repetidos.
- `tests/test_login_repositorio.py` (fixture `repo`): criar e achar pelo `sub` e pelo e-mail; `vincular_google` liga uma vez e recusa outra conta; `sub` repetido no banco é recusado; `entrar_com_google` nos três caminhos e com e-mail ligado a outra conta.
- `tests/test_login.py`: sem configuração, o botão não aparece e `/entrar` avisa; `/entrar` redireciona ao Google com `state`, `nonce` e `code_challenge`; retorno com o Google falso cria o jogador e mostra o perfil; segunda entrada volta ao mesmo jogador; `state` errado, `error=access_denied` e retorno repetido não entram; `nonce` errado não entra; **Sair** volta ao `voltz_br`; **Demo como** recusa um id que não é de demonstração; `ler_id_token` decodifica o base64url.

## Decisões
- **Sem biblioteca de OAuth:** o fluxo é curto, a biblioteca padrão basta e não há risco de mais um pacote nativo barrado pelo Smart App Control (ver `AGENTS.md`).
- **Sem conferir a assinatura do `id_token`:** ele vem direto do Google por HTTPS numa chamada do servidor, como a especificação permite. Conferir a assinatura exigiria baixar e guardar as chaves do Google e uma biblioteca de criptografia.
- **Ligar pelo e-mail só com e-mail confirmado:** evita que alguém tome um perfil criando uma conta Google com o e-mail de outra pessoa.
- **Id do jogador derivado do `sub` por hash:** o `sub` não aparece nas URLs nem nos formulários.

## Riscos
- **Credenciais do Google:** sem o cliente OAuth criado pela dupla, só os testes com o Google falso rodam. O resto do site continua igual.
- **Tela de consentimento em modo de teste:** só os e-mails cadastrados como testadores conseguem entrar. A turma precisa ser cadastrada, ou a tela publicada.
- **Tempo:** congelamento às 23h de 05/10. A ordem das fases entrega primeiro as regras e o repositório, depois as rotas e por fim a configuração do Render.
