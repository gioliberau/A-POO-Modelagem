"""Ponto de entrada do BMVC: roteamento Bottle.

Aqui ficam só as rotas e a tradução HTTP <-> controller. Regras de negócio
estão em app/controllers/application.py.

Rodar:  python route.py     (http://127.0.0.1:8080)
Variáveis opcionais: BMVC_HOST, BMVC_PORT, BMVC_DEBUG=1
"""
import json
import os
import sys
from urllib.parse import quote_plus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bottle import TEMPLATE_PATH, Bottle, redirect, request, response, run, static_file  # noqa: E402

from app.controllers.application import Application  # noqa: E402

views_path = os.path.join(BASE_DIR, "app", "views", "html")
if views_path not in TEMPLATE_PATH:
    TEMPLATE_PATH.insert(0, views_path)

app = Bottle()
ctl = Application()

COOKIE = "session_id"


# ---------------------------------------------------------------- helpers
def _json(status, body):
    response.status = status
    response.content_type = "application/json; charset=utf-8"
    return json.dumps(body, ensure_ascii=False)


def _sid():
    return request.get_cookie(COOKIE)


def _read_body():
    """Retorna (dados, veio_de_formulario, erro). Aceita JSON ou formulário HTML."""
    ctype = (request.headers.get("Content-Type") or "").lower()
    if ctype.startswith("application/x-www-form-urlencoded"):
        return {k: request.forms.getunicode(k) for k in request.forms.keys()}, True, None
    raw = request.body.read()
    if not raw.strip():
        return None, False, "Corpo da requisição vazio. Envie um JSON."
    try:
        return json.loads(raw.decode("utf-8")), False, None
    except (ValueError, UnicodeDecodeError):
        return None, False, "JSON inválido."


def _mensagem(body):
    texto = body.get("erro") or body.get("mensagem") or ""
    campos = body.get("campos")
    if campos:
        texto += " " + " ".join(f"{k}: {v}" for k, v in campos.items())
    return texto.strip()


def _wants_html():
    formato = request.query.get("formato")
    if formato:
        return formato == "html"
    return "text/html" in (request.headers.get("Accept") or "")


# ---------------------------------------------------------------- estáticos
@app.route("/static/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root=os.path.join(BASE_DIR, "app", "static"))


@app.route("/")
def index():
    return redirect("/portal")


# ---------------------------------------------------------------- PORTAL
@app.route("/portal", method="GET")
def portal_page():
    if ctl.current_user(_sid()):
        return redirect("/banco?formato=html")
    return ctl.render(
        "portal", msg=request.query.getunicode("msg"), err=request.query.getunicode("err")
    )


@app.route("/portal/cadastro", method="POST")
def portal_cadastro():
    data, is_form, erro = _read_body()
    if erro:
        status, body = 400, {"erro": erro}
    else:
        status, body = ctl.register_user(data)
    if is_form:
        if status == 201:
            return redirect("/portal?msg=" + quote_plus("Conta criada. Faça login."))
        return redirect("/portal?err=" + quote_plus(_mensagem(body)))
    return _json(status, body)


@app.route("/portal/login", method="POST")
def portal_login():
    data, is_form, erro = _read_body()
    if erro:
        status, body, sid = 400, {"erro": erro}, None
    else:
        status, body, sid = ctl.login(data)
    if sid:
        response.set_cookie(
            COOKIE, sid, httponly=True, max_age=ctl.SESSION_TTL, path="/", samesite="lax"
        )
    if is_form:
        if sid:
            return redirect("/banco?formato=html")
        return redirect("/portal?err=" + quote_plus(_mensagem(body)))
    return _json(status, body)


@app.route("/portal/logout", method="POST")
def portal_logout():
    status, body = ctl.logout(_sid())
    response.delete_cookie(COOKIE, path="/")
    if "text/html" in (request.headers.get("Accept") or "") and (
        (request.headers.get("Content-Type") or "").lower().startswith("application/x-www-form")
    ):
        return redirect("/portal?msg=" + quote_plus("Sessão encerrada."))
    return _json(status, body)


# ---------------------------------------------------------------- BANCO
@app.route("/banco", method="GET")
def banco_list():
    if _wants_html():
        html = ctl.render("banco", session_id=_sid())
        if html is None:
            return redirect("/portal?err=" + quote_plus("Faça login para acessar o banco."))
        return html
    return _json(*ctl.list_disciplinas(_sid()))


@app.route("/banco", method="POST")
def banco_create():
    data, _, erro = _read_body()
    if erro:
        # sem sessão válida a resposta correta é 401, mesmo com corpo ruim
        if not ctl.current_user(_sid()):
            return _json(*ctl.list_disciplinas(_sid()))
        return _json(400, {"erro": erro})
    return _json(*ctl.create_disciplina(_sid(), data))


@app.route("/banco/<disciplina_id:int>", method="GET")
def banco_get(disciplina_id):
    return _json(*ctl.get_disciplina(_sid(), disciplina_id))


@app.route("/banco/<disciplina_id:int>", method="PUT")
def banco_update(disciplina_id):
    data, _, erro = _read_body()
    if erro:
        if not ctl.current_user(_sid()):
            return _json(*ctl.list_disciplinas(_sid()))
        return _json(400, {"erro": erro})
    return _json(*ctl.update_disciplina(_sid(), disciplina_id, data))


@app.route("/banco/<disciplina_id:int>", method="DELETE")
def banco_delete(disciplina_id):
    return _json(*ctl.delete_disciplina(_sid(), disciplina_id))


# ---------------------------------------------------------------- erros em JSON
_MENSAGENS = {404: "Recurso não encontrado.", 405: "Método não permitido.", 500: "Erro interno do servidor."}


@app.error(404)
@app.error(405)
@app.error(500)
def erro_json(err):
    response.content_type = "application/json; charset=utf-8"
    return json.dumps({"erro": _MENSAGENS.get(err.status_code, "Erro.")}, ensure_ascii=False)


if __name__ == "__main__":
    run(
        app,
        host=os.environ.get("BMVC_HOST", "127.0.0.1"),
        port=int(os.environ.get("BMVC_PORT", "8080")),
        debug=os.environ.get("BMVC_DEBUG") == "1",
    )
