import json
import os
import unittest

from tests.base import TempDBCase
from app.controllers.datarecord import DataRecord, DataRecordError, DuplicateError
from app.models import Disciplina, User_account


def disc(codigo="ABC123", nome="Cálculo"):
    return Disciplina(codigo=codigo, nome=nome, creditos=4, departamento="MAT")


class DataRecordTests(TempDBCase):
    def test_persiste_entre_instancias(self):
        DataRecord(self.tmp).add_disciplina(disc())
        itens = DataRecord(self.tmp).list_disciplinas()  # "reinício"
        self.assertEqual([d.codigo for d in itens], ["ABC123"])

    def test_ids_nao_sao_reutilizados(self):
        r = DataRecord(self.tmp)
        a = r.add_disciplina(disc("AAA111"))
        r.delete_disciplina(a.id)
        b = r.add_disciplina(disc("BBB222"))
        self.assertNotEqual(a.id, b.id)

    def test_codigo_duplicado(self):
        r = DataRecord(self.tmp)
        r.add_disciplina(disc())
        with self.assertRaises(DuplicateError):
            r.add_disciplina(disc())

    def test_update_codigo_duplicado_e_inexistente(self):
        r = DataRecord(self.tmp)
        a = r.add_disciplina(disc("AAA111"))
        r.add_disciplina(disc("BBB222"))
        with self.assertRaises(DuplicateError):
            r.update_disciplina(a.id, {"codigo": "BBB222"})
        self.assertEqual(r.update_disciplina(a.id, {"codigo": "AAA111", "nome": "Novo"}).nome, "Novo")
        self.assertIsNone(r.update_disciplina(999, {"nome": "x"}))

    def test_delete(self):
        r = DataRecord(self.tmp)
        a = r.add_disciplina(disc())
        self.assertTrue(r.delete_disciplina(a.id))
        self.assertFalse(r.delete_disciplina(a.id))

    def test_email_unico_e_busca(self):
        r = DataRecord(self.tmp)
        r.add_user(User_account.create("Ana", "ana@x.com", "senhaforte1"))
        with self.assertRaises(DuplicateError):
            r.add_user(User_account.create("Outra", "ana@x.com", "senhaforte2"))
        self.assertEqual(r.find_user_by_email("ana@x.com").nome, "Ana")
        self.assertIsNone(r.find_user_by_email("nao@x.com"))
        self.assertEqual(r.find_user_by_id(1).email, "ana@x.com")

    def test_arquivo_corrompido(self):
        r = DataRecord(self.tmp)
        with open(os.path.join(self.tmp, "disciplinas.json"), "w") as f:
            f.write("{quebrado")
        with self.assertRaises(DataRecordError):
            r.list_disciplinas()

    def test_sem_arquivos_temporarios_sobrando(self):
        r = DataRecord(self.tmp)
        r.add_disciplina(disc())
        self.assertEqual(sorted(os.listdir(self.tmp)), ["disciplinas.json"])

    def test_json_legivel_com_acentos(self):
        DataRecord(self.tmp).add_disciplina(disc(nome="Orientação a Objetos"))
        with open(os.path.join(self.tmp, "disciplinas.json"), encoding="utf-8") as f:
            self.assertIn("Orientação", f.read())
            f.seek(0)
            json.load(f)


if __name__ == "__main__":
    unittest.main()
