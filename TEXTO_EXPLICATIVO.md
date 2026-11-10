# Texto explicativo — Banco de Disciplinas (UnB FCTE)

## Finalidade e problema
Informações sobre disciplinas costumam ficar espalhadas em planilhas e
documentos. Este sistema reúne em um só lugar os dados básicos de cada
disciplina ofertada pela FCTE (código, nome, créditos, departamento e curso),
com acesso restrito a usuários cadastrados. Não substitui o SIGAA: é uma
aplicação pequena, criada para exercitar a arquitetura BMVC.

## Arquitetura BMVC
BMVC combina o microframework **Bottle** com o padrão **MVC**. O `route.py`
cria a aplicação Bottle e apenas liga cada URL a um método do controller, sem
regras de negócio. O **controller** `Application` valida a autenticação, aplica
as regras e devolve o resultado. Os **models** (`User_account` e `Disciplina`)
descrevem os dados e suas validações. A **persistência** fica no `DataRecord`,
que grava os objetos em arquivos JSON. As **views** (`portal.tpl` e `banco.tpl`)
geram o HTML. Assim, trocar a forma de armazenamento não afeta as rotas, e as
regras podem ser testadas sem subir o servidor.

## Recurso portal
Cuida do acesso. O modelo `User_account` guarda nome, e-mail (único) e o hash
da senha (PBKDF2-HMAC-SHA256 com salt), nunca a senha em texto puro. As rotas
`/portal/cadastro`, `/portal/login` e `/portal/logout` criam a conta, abrem a
sessão e a encerram. No login, o servidor gera um identificador aleatório,
guardado em memória, e o envia em um cookie HttpOnly (`session_id`); o cURL o
reutiliza com `-c` e `-b`. A sessão expira em uma hora.

## Recurso banco
Gerencia objetos `Disciplina`. Toda operação começa por checar a sessão; sem
ela, a resposta é 401. O **CREATE** (`POST /banco`) valida os dados e impede
código repetido (409). O **READ** lista (`GET /banco`) ou consulta por id
(`GET /banco/<id>`), e também existe como página HTML dentro do próprio sistema, em um
painel administrativo que permite cadastrar, editar e excluir disciplinas pelo navegador
(o JavaScript apenas chama a mesma API usada pelo cURL).
O **UPDATE** (`PUT /banco/<id>`) altera só os campos enviados. O **DELETE**
(`DELETE /banco/<id>`) remove a disciplina. Disciplinas inexistentes retornam 404.

## Responsabilidade das classes
- `User_account`: valida cadastro, gera e confere o hash da senha.
- `Disciplina`: valida e normaliza os atributos (código em maiúsculas, créditos de 1 a 30).
- `DataRecord`: lê e grava JSON de forma atômica; garante e-mail e código únicos.
- `Application`: autenticação, sessões e regras do CRUD; devolve (status, corpo).
- `route.py`: rotas Bottle, leitura do corpo da requisição, cookies e respostas JSON/HTML.

## Tecnologias
Python 3, Bottle (única dependência externa), JSON para persistência e para a
API, cURL para os testes, `unittest` para os testes automatizados, Git/GitHub
para versionamento.

## Limitações
Sem proteção CSRF e sem limite de tentativas de login. O armazenamento em JSON
não é adequado a uso concorrente intenso. As sessões somem ao reiniciar o servidor.
