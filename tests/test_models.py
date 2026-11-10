import unittest

from tests.base import TempDBCase  # noqa: F401  (define BMVC_PBKDF2_ITER)
from app.models import Disciplina, User_account, ValidationError


class UserAccountTests(unittest.TestCase):
    def test_hash_nao_guarda_texto_puro_e_verifica(self):
        u = User_account.create("Ana", "ana@x.com", "senhaforte1")
        self.assertNotIn("senhaforte1", u.senha_hash)
        self.assertTrue(u.verify_password("senhaforte1"))
        self.assertFalse(u.verify_password("outra-senha"))

    def test_salt_diferente_por_usuario(self):
        a = User_account.create("A", "a@x.com", "senhaforte1")
        b = User_account.create("B", "b@x.com", "senhaforte1")
        self.assertNotEqual(a.senha_hash, b.senha_hash)

    def test_public_dict_sem_hash(self):
        u = User_account.create("Ana", "ana@x.com", "senhaforte1")
        self.assertNotIn("senha_hash", u.to_public_dict())

    def test_validacao_cadastro(self):
        ok = User_account.validate_registration({"nome": " Ana ", "email": "ANA@X.com ", "senha": "12345678"})
        self.assertEqual(ok["email"], "ana@x.com")
        self.assertEqual(ok["nome"], "Ana")
        with self.assertRaises(ValidationError) as ctx:
            User_account.validate_registration({"nome": "A", "email": "ruim", "senha": "123"})
        self.assertEqual(set(ctx.exception.errors), {"nome", "email", "senha"})
        with self.assertRaises(ValidationError):
            User_account.validate_registration([])

    def test_hash_malformado_nao_autentica(self):
        self.assertFalse(User_account.check_hash("x", "lixo"))


class DisciplinaTests(unittest.TestCase):
    def test_create_valido_normaliza(self):
        c = Disciplina.validate({"codigo": " abc123 ", "nome": "Cálculo", "creditos": 4, "departamento": "MAT"})
        self.assertEqual(c["codigo"], "ABC123")
        self.assertEqual(c["curso"], "")

    def test_create_invalido(self):
        with self.assertRaises(ValidationError) as ctx:
            Disciplina.validate({"codigo": "!", "nome": "", "creditos": True, "departamento": 3})
        self.assertEqual(set(ctx.exception.errors), {"codigo", "nome", "creditos", "departamento"})

    def test_creditos_limites_e_tipo(self):
        base = {"codigo": "ABC123", "nome": "Física", "departamento": "FIS"}
        for ruim in (0, 31, -1, 2.5, "x", None):
            with self.assertRaises(ValidationError):
                Disciplina.validate({**base, "creditos": ruim})
        self.assertEqual(Disciplina.validate({**base, "creditos": "4"})["creditos"], 4)

    def test_partial(self):
        self.assertEqual(Disciplina.validate({"nome": "Novo nome"}, partial=True), {"nome": "Novo nome"})
        with self.assertRaises(ValidationError):
            Disciplina.validate({}, partial=True)
        with self.assertRaises(ValidationError):
            Disciplina.validate({"creditos": 99}, partial=True)

    def test_nao_dict(self):
        with self.assertRaises(ValidationError):
            Disciplina.validate("texto")


if __name__ == "__main__":
    unittest.main()
