#!/usr/bin/env bash
# Executa os 12 cenários de TESTES_CURL.md contra o servidor em execução.
# Uso:  ./scripts/testes_curl.sh            (BASE padrão: http://127.0.0.1:8080)
#       BASE=http://127.0.0.1:9000 ./scripts/testes_curl.sh
set -u
BASE="${BASE:-http://127.0.0.1:8080}"
JAR="$(mktemp)"
EMAIL="aluno$(date +%s)@exemplo.com"   # e-mail novo a cada execução
COD="T$(date +%s | tail -c 8)"         # código novo a cada execução
FALHAS=0

req() {  # req <status_esperado> <titulo> <args do curl...>
  local esperado="$1" titulo="$2"; shift 2
  local out status corpo
  out=$(curl -s -w '\n%{http_code}' -b "$JAR" -c "$JAR" "$@")
  status="${out##*$'\n'}"; corpo="${out%$'\n'*}"
  if [ "$status" = "$esperado" ]; then r="OK  "; else r="FALHA"; FALHAS=$((FALHAS+1)); fi
  printf '%s %s -> HTTP %s (esperado %s)\n      %s\n' "$r" "$titulo" "$status" "$esperado" "$corpo"
  LAST="$corpo"
}
J='Content-Type: application/json'

req 401 "03 banco sem login"            "$BASE/banco"
req 201 "01 cadastro de usuário"        -X POST "$BASE/portal/cadastro" -H "$J" -d "{\"nome\":\"Aluno Teste\",\"email\":\"$EMAIL\",\"senha\":\"senhaforte1\"}"
req 409 "01b cadastro e-mail repetido"  -X POST "$BASE/portal/cadastro" -H "$J" -d "{\"nome\":\"Aluno Teste\",\"email\":\"$EMAIL\",\"senha\":\"senhaforte1\"}"
req 401 "02b login com senha errada"    -X POST "$BASE/portal/login"    -H "$J" -d "{\"email\":\"$EMAIL\",\"senha\":\"errada1234\"}"
req 200 "02 login"                      -X POST "$BASE/portal/login"    -H "$J" -d "{\"email\":\"$EMAIL\",\"senha\":\"senhaforte1\"}"
req 200 "04 listar disciplinas"         "$BASE/banco"
req 201 "05 cadastrar disciplina"       -X POST "$BASE/banco" -H "$J" -d "{\"codigo\":\"$COD\",\"nome\":\"Orientação a Objetos\",\"creditos\":4,\"departamento\":\"Exemplo\",\"curso\":\"Engenharia de Software\"}"
ID=$(printf '%s' "$LAST" | sed -n 's/.*"id": *\([0-9]*\).*/\1/p' | head -1)
req 200 "06 consultar por id"           "$BASE/banco/$ID"
req 200 "07 atualizar (PUT)"            -X PUT "$BASE/banco/$ID" -H "$J" -d '{"creditos":6}'
req 409 "09 código duplicado"           -X POST "$BASE/banco" -H "$J" -d "{\"codigo\":\"$COD\",\"nome\":\"Outra\",\"creditos\":4,\"departamento\":\"Exemplo\"}"
req 400 "09b dados inválidos"           -X POST "$BASE/banco" -H "$J" -d '{"codigo":"!","creditos":0}'
req 200 "08 excluir"                    -X DELETE "$BASE/banco/$ID"
req 404 "10a consultar inexistente"     "$BASE/banco/$ID"
req 404 "10b excluir inexistente"       -X DELETE "$BASE/banco/$ID"
req 200 "11 logout"                     -X POST "$BASE/portal/logout"
req 401 "12 banco após logout"          "$BASE/banco"

rm -f "$JAR"
echo; [ "$FALHAS" -eq 0 ] && echo "Todos os cenários passaram." || echo "$FALHAS cenário(s) falharam."
exit "$FALHAS"
