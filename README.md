# Banco de Disciplinas — UnB FCTE (BMVC)

Sistema acadêmico simplificado para cadastrar, consultar, atualizar e excluir
disciplinas da FCTE/UnB, **pelo navegador ou por cURL**. Atividade de Orientação a Objetos, **Nível 2 do BMVC**:
dois recursos (`portal` e `banco`), login com o modelo `User_account`, CRUD via
cURL e READ implementado no próprio sistema.

## Requisitos do enunciado × onde estão

| Requisito | Onde |
|---|---|
| Framework BMVC (Bottle + MVC) | `route.py`, `app/` |
| Recursos `portal` e `banco` | rotas `/portal/*` e `/banco/*` em `route.py` |
| Modelo `User_account` | `app/models/user_account.py` |
| Só autenticados acessam `banco` | `Application.current_user` em todas as operações do banco |
| `banco` lista os objetos | `GET /banco` (JSON) e `GET /banco?formato=html` (página) |
| Objeto com ≥ 2 atributos | `Disciplina`: codigo, nome, creditos, departamento, curso |
| CRUD via cURL | `TESTES_CURL.md` e `scripts/testes_curl.sh` |
| READ no próprio sistema | página HTML `app/views/html/banco.tpl` |
| CRUD também pelo navegador | `app/static/js/banco.js` (usa a mesma API) |
| CREATE e DELETE (+ UPDATE extra) | `POST /banco`, `DELETE /banco/<id>`, `PUT /banco/<id>` |

## Arquitetura (BMVC = Bottle + MVC)

```
route.py                       # Bottle: rotas e tradução HTTP <-> controller
app/
├── models/
│   ├── user_account.py        # User_account: validação, hash de senha
│   ├── disciplina.py          # Disciplina: validação dos atributos
│   └── errors.py              # ValidationError
├── controllers/
│   ├── application.py         # Controller: regras do portal e do banco, sessões
│   ├── datarecord.py          # Persistência em JSON (DataRecord)
│   └── db/                    # users.json e disciplinas.json (gerados em execução)
├── views/html/
│   ├── portal.tpl             # login e cadastro
│   └── banco.tpl              # painel administrativo (listagem + formulários)
└── static/
    ├── css/style.css          # identidade visual UnB/FCTE, layout responsivo
    ├── js/banco.js            # cadastro, edição, exclusão e mensagens (via API)
    └── img/logo-unb-fcte.png  # logo UnB | FCTE
seed.py                        # disciplinas de exemplo (opcional)
scripts/testes_curl.sh         # roda os 12 cenários de cURL
tests/                         # unittest + e2e_navegador.py (Playwright, opcional)
```

**Interpretação arquitetural adotada.** Não encontrei a documentação oficial do
framework. Segui a estrutura de um projeto de aluno baseado no template da
disciplina (repositório público `Gustavormq/BMVC`): `route.py` na raiz com
`app = Bottle()` e `ctl = Application()`, controller `Application` e
`DataRecord` em `app/controllers/`, modelos em `app/models/`, views `.tpl` em
`app/views/html/`, estáticos em `app/static/`, persistência em JSON e sessão por
cookie `session_id`. Não consegui ler o código de `application.py` e
`datarecord.py` desse repositório (acesso automatizado bloqueado), então os
**nomes de métodos internos são meus**. Confira com o material do professor.

## Interface web (painel administrativo)

Depois do login, `http://127.0.0.1:8080/banco?formato=html` mostra o painel:

- **Listagem** em tabela, com coluna **Ações** (Editar e Excluir) em cada linha.
- **+ Nova disciplina**: abre um formulário com código, nome, créditos, departamento e curso.
- **Editar**: abre o mesmo formulário já preenchido com os dados atuais.
- **Excluir**: sempre pede confirmação (“Esta ação não pode ser desfeita”).
- **Mensagens** de sucesso e de erro após cada operação; erros de validação ou de código
  duplicado aparecem junto do campo correspondente.
- Se a sessão expirar, o painel leva de volta ao portal com um aviso.
- Layout responsivo: tabela no computador, cartões no celular. Cores e logo da UnB | FCTE.

O painel **não tem regra de negócio própria**: o JavaScript chama a API já existente
(`GET/POST /banco`, `PUT/DELETE /banco/<id>`) com o cookie de sessão do navegador, então
validação, autenticação e persistência continuam sendo as do controller `Application`.
Os textos são inseridos na tela como texto (não como HTML), evitando injeção de código.
O cURL continua funcionando exatamente como antes.

## Instalação e execução

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # só o Bottle
python seed.py                           # opcional: disciplinas de exemplo
python route.py                          # http://127.0.0.1:8080
```

Variáveis opcionais: `BMVC_HOST`, `BMVC_PORT`, `BMVC_DEBUG=1`, `BMVC_DB_DIR`.

Em outro terminal: siga `TESTES_CURL.md` ou rode `./scripts/testes_curl.sh`.
No navegador: abra `http://127.0.0.1:8080/portal`, crie a conta, entre e veja a lista.

## Testes automatizados

```bash
python -m unittest discover -s tests -t . -v
```

`tests/test_http.py` sobe o servidor de verdade e exige o Bottle instalado
(sem ele, é ignorado automaticamente).

Teste da interface no navegador (opcional, usa o Chromium via Playwright):

```bash
pip install playwright && playwright install chromium
python route.py &                       # servidor em http://127.0.0.1:8080
python tests/e2e_navegador.py           # cadastra, edita, exclui, testa erros e celular
python tests/e2e_navegador.py http://127.0.0.1:8080 capturas/   # salva capturas de tela
```

## Decisões

- **Bottle**: é o "B" do BMVC; única dependência.
- **JSON em vez de SQLite**: é a persistência do template BMVC (`DataRecord`).
  Escrita atômica e trava de thread. Não use com vários processos em paralelo.
- **PBKDF2-HMAC-SHA256** (biblioteca padrão) com salt aleatório para as senhas.
- **Sessão por cookie** (`session_id`, HttpOnly): o cURL guarda com `-c` e reenvia com `-b`.
  As sessões ficam em memória: reiniciar o servidor exige novo login (os dados persistem).
- `GET /banco` devolve **HTML** se o cliente pedir `text/html` (navegador) ou
  `?formato=html`; caso contrário, **JSON** (cURL).

## Limitações conhecidas

- Sem proteção CSRF nem limite de tentativas de login (fora do escopo da atividade).
- O banco em JSON não serve para uso concorrente real.
- A interface exige JavaScript habilitado para cadastrar, editar e excluir (a listagem aparece sem ele).
- Os formulários do portal (login/cadastro) e o botão Sair são formulários HTML comuns, sem JavaScript.
