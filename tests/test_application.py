import unittest

from tests.base import TempDBCase
from app.controllers.application import Application
from app.controllers.datarecord import DataRecord

USER = {"nome": "Ana", "email": "ana@x.com", "senha": "senhaforte1"}
DISC = {"codigo": "abc123", "nome": "Cálculo 1", "creditos": 6, "departamento": "MAT", "curso": "Eng"}


class AppCase(TempDBCase):
    def setUp(self):
        super().setUp()
        self.now = 1000.0
        self.app = Application(DataRecord(self.tmp), clock=lambda: self.now)

    def logar(self):
        self.app.register_user(USER)
        status, _, sid = self.app.login({"email": USER["email"], "senha": USER["senha"]})
        self.assertEqual(status, 200)
        return sid


class PortalTests(AppCase):
    def test_cadastro_ok_e_sem_hash_na_resposta(self):
        status, body = self.app.register_user(USER)
        self.assertEqual(status, 201)
        self.assertNotIn("senha", str(body))

    def test_cadastro_email_duplicado_case_insensitive(self):
        self.app.register_user(USER)
        status, _ = self.app.register_user({**USER, "email": "ANA@X.COM"})
        self.assertEqual(status, 409)

    def test_cadastro_invalido(self):
        status, body = self.app.register_user({"nome": "A"})
        self.assertEqual(status, 400)
        self.assertIn("email", body["campos"])

    def test_login_ok_e_falhas(self):
        self.app.register_user(USER)
        status, _, sid = self.app.login({"email": "ANA@x.com", "senha": USER["senha"]})
        self.assertEqual((status, bool(sid)), (200, True))
        for dados in ({"email": USER["email"], "senha": "errada123"}, {"email": "no@x.com", "senha": "senhaforte1"}):
            status, _, sid = self.app.login(dados)
            self.assertEqual((status, sid), (401, None))
        self.assertEqual(self.app.login({})[0], 400)
        self.assertEqual(self.app.login(None)[0], 400)

    def test_logout_invalida_sessao(self):
        sid = self.logar()
        self.assertIsNotNone(self.app.current_user(sid))
        self.assertEqual(self.app.logout(sid)[0], 200)
        self.assertIsNone(self.app.current_user(sid))
        self.assertEqual(self.app.logout(sid)[0], 200)  # idempotente

    def test_sessao_expira(self):
        sid = self.logar()
        self.now += Application.SESSION_TTL + 1
        self.assertIsNone(self.app.current_user(sid))

    def test_sessao_falsa(self):
        self.assertIsNone(self.app.current_user("inventado"))
        self.assertIsNone(self.app.current_user(None))


class BancoTests(AppCase):
    def test_tudo_exige_autenticacao(self):
        for status, _ in (
            self.app.list_disciplinas(None),
            self.app.get_disciplina(None, 1),
            self.app.create_disciplina(None, DISC),
            self.app.update_disciplina("x", 1, {"nome": "Nome ok"}),
            self.app.delete_disciplina("x", 1),
        ):
            self.assertEqual(status, 401)
        sid = self.logar()
        self.app.logout(sid)
        self.assertEqual(self.app.list_disciplinas(sid)[0], 401)

    def test_crud_completo(self):
        sid = self.logar()
        self.assertEqual(self.app.list_disciplinas(sid)[1], {"total": 0, "disciplinas": []})

        status, body = self.app.create_disciplina(sid, DISC)
        self.assertEqual(status, 201)
        did = body["disciplina"]["id"]
        self.assertEqual(body["disciplina"]["codigo"], "ABC123")

        self.assertEqual(self.app.list_disciplinas(sid)[1]["total"], 1)
        self.assertEqual(self.app.get_disciplina(sid, did)[0], 200)

        status, body = self.app.update_disciplina(sid, did, {"creditos": 4})
        self.assertEqual((status, body["disciplina"]["creditos"]), (200, 4))
        self.assertEqual(body["disciplina"]["nome"], "Cálculo 1")

        self.assertEqual(self.app.delete_disciplina(sid, did)[0], 200)
        self.assertEqual(self.app.get_disciplina(sid, did)[0], 404)
        self.assertEqual(self.app.delete_disciplina(sid, did)[0], 404)

    def test_erros(self):
        sid = self.logar()
        self.app.create_disciplina(sid, DISC)
        self.assertEqual(self.app.create_disciplina(sid, DISC)[0], 409)
        self.assertEqual(self.app.create_disciplina(sid, {"codigo": "X"})[0], 400)
        self.assertEqual(self.app.create_disciplina(sid, None)[0], 400)
        self.assertEqual(self.app.update_disciplina(sid, 999, {"nome": "Nome ok"})[0], 404)
        self.assertEqual(self.app.update_disciplina(sid, 1, {})[0], 400)
        self.assertEqual(self.app.update_disciplina(sid, 1, {"creditos": 0})[0], 400)
        self.app.create_disciplina(sid, {**DISC, "codigo": "OUT999"})
        self.assertEqual(self.app.update_disciplina(sid, 2, {"codigo": "abc123"})[0], 409)

    def test_dados_persistem_apos_reiniciar_app(self):
        sid = self.logar()
        self.app.create_disciplina(sid, DISC)
        novo = Application(DataRecord(self.tmp), clock=lambda: self.now)
        # sessões são em memória: precisa logar de novo, mas os dados continuam
        _, _, sid2 = novo.login({"email": USER["email"], "senha": USER["senha"]})
        self.assertEqual(novo.list_disciplinas(sid2)[1]["total"], 1)


if __name__ == "__main__":
    unittest.main()
