"""Teste de integração HTTP: sobe route.py de verdade e fala com ele por sockets.

Requer o Bottle instalado (pip install -r requirements.txt); sem ele, é ignorado.
"""
import http.cookiejar
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from wsgiref.simple_server import WSGIRequestHandler, make_server

os.environ.setdefault("BMVC_PBKDF2_ITER", "1000")

try:
    import bottle  # noqa: F401
    HAS_BOTTLE = True
except ImportError:
    HAS_BOTTLE = False


class _Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


@unittest.skipUnless(HAS_BOTTLE, "Bottle não instalado")
class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        os.environ["BMVC_DB_DIR"] = cls.tmp
        import route  # importa depois de definir BMVC_DB_DIR

        cls.server = make_server("127.0.0.1", 0, route.app, handler_class=_Quiet)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        os.environ.pop("BMVC_DB_DIR", None)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, method, path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json"} if body is not None else {}
        h.update(headers or {})
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with self.opener.open(req) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def test_fluxo_completo(self):
        user = {"nome": "Ana", "email": "ana@x.com", "senha": "senhaforte1"}
        disc = {"codigo": "ABC123", "nome": "Cálculo", "creditos": 4, "departamento": "MAT"}

        self.assertEqual(self.call("GET", "/banco")[0], 401)
        self.assertEqual(self.call("POST", "/banco", disc)[0], 401)
        self.assertEqual(self.call("POST", "/portal/cadastro", user)[0], 201)
        self.assertEqual(self.call("POST", "/portal/cadastro", user)[0], 409)
        self.assertEqual(self.call("POST", "/portal/login", {**user, "senha": "errada123"})[0], 401)
        self.assertEqual(self.call("POST", "/portal/login", user)[0], 200)

        status, body = self.call("POST", "/banco", disc)
        self.assertEqual(status, 201)
        did = json.loads(body)["disciplina"]["id"]
        self.assertEqual(self.call("POST", "/banco", disc)[0], 409)
        self.assertEqual(json.loads(self.call("GET", "/banco")[1])["total"], 1)
        self.assertEqual(self.call("GET", f"/banco/{did}")[0], 200)
        self.assertEqual(self.call("PUT", f"/banco/{did}", {"creditos": 6})[0], 200)
        self.assertEqual(self.call("GET", "/banco/999")[0], 404)
        self.assertEqual(self.call("POST", "/banco", None)[0], 400)

        status, html = self.call("GET", "/banco", headers={"Accept": "text/html"})
        self.assertEqual(status, 200)
        self.assertIn("ABC123", html)

        self.assertEqual(self.call("DELETE", f"/banco/{did}")[0], 200)
        self.assertEqual(self.call("DELETE", f"/banco/{did}")[0], 404)
        self.assertEqual(self.call("POST", "/portal/logout")[0], 200)
        self.assertEqual(self.call("GET", "/banco")[0], 401)

    def test_json_invalido(self):
        req = urllib.request.Request(
            self.base + "/portal/login", data=b"{nao-json", method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
