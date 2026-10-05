# Login com a conta Google

**Data:** 05/10/2026 · **Status:** proposta, sem código ainda · **Branch:** `008-login-google` · **Detalhes:** `specs/008-login-google/`

## O quê
Qualquer pessoa entra no CircuitCrash com a própria conta Google, pelo botão **Entrar com Google** do cabeçalho. Na primeira vez, o sistema cria um jogador novo com o nome e o e-mail da conta Google: começa sem Fagulhas, sem avatar e com rating 1200. Nas vezes seguintes, volta para o mesmo jogador. Quem entrou vê **Sair** no lugar do seletor **Demo como**, e tudo o que fizer (comprar, trocar de avatar, jogar) fica no próprio perfil.

Os perfis de demonstração continuam funcionando sem login, para a apresentação não depender da conta de ninguém.

## Por quê
Até aqui, qualquer pessoa joga com os perfis de exemplo, e o espaço para a conta Google no cadastro dos jogadores (spec 002) está vazio. Com o login, cada pessoa da turma tem o próprio perfil, as próprias Fagulhas e o próprio lugar no ranking. O Google guarda a senha: o CircuitCrash nunca vê nem guarda senha.

## Critérios de aceitação

### Entrar
1. **Dado** que o login Google está configurado, **quando** clico em **Entrar com Google** e autorizo na tela do Google, **então** volto ao CircuitCrash já como o meu jogador.
2. **Dado** que é a primeira vez que entro, **então** é criado um jogador com o meu nome do Google como apelido (sem repetir o apelido de outro jogador), o meu e-mail, 0 Fagulhas, rating 1200 e nenhum avatar.
3. **Dado** que já entrei antes, **quando** entro de novo, **então** volto ao mesmo jogador, com as Fagulhas, os avatares e as partidas que eu tinha.
4. **Dado** que já existe um jogador com o meu e-mail e sem conta Google ligada, **quando** entro, **então** a minha conta Google é ligada a ele, sem criar outro.
5. Só entra quem tem o e-mail confirmado pelo Google.

### Segurança
6. O retorno do Google só é aceito se vier da mesma tentativa de login que começou neste navegador; caso contrário, nada acontece e aparece um aviso.
7. Se eu cancelar na tela do Google ou algo der errado, volto ao início com um aviso, sem entrar.
8. Nenhuma senha é guardada, e o identificador e a chave do login Google ficam só no `.env` e nas variáveis do serviço publicado, nunca no repositório.
9. O seletor **Demo como** só troca para os perfis de demonstração: ninguém entra no perfil de outra pessoa por ele.

### Sair e demonstração
10. **Quando** clico em **Sair**, **então** volto a ver o perfil de demonstração padrão.
11. **Dado** que o login Google não está configurado, **então** o botão **Entrar com Google** não aparece e todo o resto funciona como antes.
12. Funciona no celular, a partir de 360 px, e mesmo se o HTMX não carregar.
13. Funciona com os dados em memória e com o banco; `pytest`, `ruff` e `mypy` passam.

## Fora do escopo
- Outros provedores de login (GitHub, Microsoft, e-mail e senha).
- Escolher ou trocar o apelido depois de entrar.
- Apagar a conta.
- Guardar as contas criadas na versão publicada entre reinícios: no plano gratuito, o banco volta ao exemplo a cada reinício (spec 004).
- Painel de administração e permissões diferentes por jogador.
