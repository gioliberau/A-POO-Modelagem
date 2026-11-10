# Testes com cURL

Servidor rodando em `http://127.0.0.1:8080` (`python route.py`).
Todos os comandos usam `-b cookies.txt -c cookies.txt`: o **cookie de sessão**
`session_id` recebido no login é gravado no arquivo e reenviado nas requisições
seguintes. Sem ele, o `banco` responde **401**.

Para rodar tudo de uma vez: `./scripts/testes_curl.sh`.

```bash
BASE=http://127.0.0.1:8080
rm -f cookies.txt
```

## 3. Banco sem autenticação → 401
```bash
curl -i $BASE/banco
```
```json
{"erro": "Não autenticado. Faça login em /portal/login."}
```

## 1. Cadastro de usuário → 201
```bash
curl -i -X POST $BASE/portal/cadastro -H 'Content-Type: application/json' \
  -d '{"nome":"Aluno Teste","email":"aluno@exemplo.com","senha":"senhaforte1"}'
```
```json
{"mensagem": "Usuário cadastrado.", "usuario": {"id": 1, "nome": "Aluno Teste", "email": "aluno@exemplo.com"}}
```
Repetindo o mesmo e-mail → **409** `{"erro": "Já existe um usuário com este e-mail."}`.
Dados inválidos (nome curto, e-mail ruim, senha < 8) → **400** com `campos`.

## 2. Login → 200 (grava o cookie)
```bash
curl -i -c cookies.txt -X POST $BASE/portal/login -H 'Content-Type: application/json' \
  -d '{"email":"aluno@exemplo.com","senha":"senhaforte1"}'
```
```json
{"mensagem": "Login realizado.", "usuario": {"id": 1, "nome": "Aluno Teste", "email": "aluno@exemplo.com"}}
```
Senha errada ou e-mail inexistente → **401** `{"erro": "Credenciais inválidas."}`.

## 4. Listar disciplinas → 200
```bash
curl -b cookies.txt -c cookies.txt $BASE/banco
```
```json
{"total": 0, "disciplinas": []}
```
Versão HTML (READ no sistema): abra `http://127.0.0.1:8080/portal` no navegador, faça login,
ou use `curl -b cookies.txt "$BASE/banco?formato=html"`.

## 5. Cadastrar disciplina → 201
```bash
curl -b cookies.txt -c cookies.txt -X POST $BASE/banco -H 'Content-Type: application/json' \
  -d '{"codigo":"ABC0001","nome":"Orientação a Objetos","creditos":4,"departamento":"Exemplo","curso":"Engenharia de Software"}'
```
```json
{"mensagem": "Disciplina cadastrada.", "disciplina": {"id": 1, "codigo": "ABC0001", "nome": "Orientação a Objetos", "creditos": 4, "departamento": "Exemplo", "curso": "Engenharia de Software"}}
```
Dados inválidos → **400** com o detalhe por campo em `campos`.

## 6. Consultar por id → 200
```bash
curl -b cookies.txt -c cookies.txt $BASE/banco/1
```
```json
{"disciplina": {"id": 1, "codigo": "ABC0001", "nome": "Orientação a Objetos", "creditos": 4, "departamento": "Exemplo", "curso": "Engenharia de Software"}}
```

## 7. Atualizar → 200 (só os campos enviados mudam)
```bash
curl -b cookies.txt -c cookies.txt -X PUT $BASE/banco/1 -H 'Content-Type: application/json' \
  -d '{"creditos":6}'
```
```json
{"mensagem": "Disciplina atualizada.", "disciplina": {"id": 1, "codigo": "ABC0001", "nome": "Orientação a Objetos", "creditos": 6, "departamento": "Exemplo", "curso": "Engenharia de Software"}}
```

## 9. Código duplicado → 409
```bash
curl -b cookies.txt -c cookies.txt -X POST $BASE/banco -H 'Content-Type: application/json' \
  -d '{"codigo":"ABC0001","nome":"Outra","creditos":4,"departamento":"Exemplo"}'
```
```json
{"erro": "Já existe uma disciplina com o código ABC0001."}
```

## 8. Excluir → 200
```bash
curl -b cookies.txt -c cookies.txt -X DELETE $BASE/banco/1
```
```json
{"mensagem": "Disciplina 1 excluída."}
```

## 10. Consultar ou excluir inexistente → 404
```bash
curl -b cookies.txt -c cookies.txt $BASE/banco/1
curl -b cookies.txt -c cookies.txt -X DELETE $BASE/banco/1
```
```json
{"erro": "Disciplina 1 não encontrada."}
```

## 11. Logout → 200
```bash
curl -b cookies.txt -c cookies.txt -X POST $BASE/portal/logout
```
```json
{"mensagem": "Sessão encerrada."}
```

## 12. Banco após logout → 401
```bash
curl -b cookies.txt -c cookies.txt -i $BASE/banco
```
```json
{"erro": "Não autenticado. Faça login em /portal/login."}
```

## Tabela de status

| Situação | Status |
|---|---|
| Sucesso (consulta, listagem, atualização, exclusão, login, logout) | 200 |
| Criação (usuário, disciplina) | 201 |
| JSON inválido ou dados que não passam na validação | 400 |
| Sem sessão válida / credenciais erradas | 401 |
| Disciplina inexistente / rota inexistente | 404 |
| Método não permitido | 405 |
| E-mail ou código duplicado | 409 |
