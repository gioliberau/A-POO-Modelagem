"""DataRecord: camada de persistência do BMVC (arquivos JSON em app/controllers/db/).

Segue a convenção do template BMVC: os objetos do Model são gravados em
arquivos .json e lidos de volta como objetos. Cada coleção é um arquivo:

    users.json        -> User_account
    disciplinas.json  -> Disciplina

Formato de cada arquivo:  {"next_id": <int>, "items": [ {...}, ... ]}

Escrita atômica (arquivo temporário + os.replace) e trava de thread, para
que uma falha no meio da gravação não corrompa o arquivo.
O diretório pode ser trocado com a variável de ambiente BMVC_DB_DIR.
"""
import json
import os
import tempfile
import threading

from app.models.disciplina import Disciplina
from app.models.user_account import User_account

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_DIR = os.path.join(BASE_DIR, "db")


class DataRecordError(Exception):
    """Arquivo de dados ilegível ou inválido."""


class DuplicateError(Exception):
    """Violação de unicidade (e-mail de usuário ou código de disciplina)."""

    def __init__(self, field):
        super().__init__(f"Valor duplicado em '{field}'")
        self.field = field


class DataRecord:
    def __init__(self, db_dir=None):
        self.db_dir = db_dir or os.environ.get("BMVC_DB_DIR") or DEFAULT_DB_DIR
        os.makedirs(self.db_dir, exist_ok=True)
        self._lock = threading.RLock()

    # ---------- baixo nível ----------
    def _path(self, collection):
        return os.path.join(self.db_dir, collection + ".json")

    def _load(self, collection):
        path = self._path(collection)
        if not os.path.exists(path):
            return {"next_id": 1, "items": []}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as exc:
            raise DataRecordError(f"Não foi possível ler {path}: {exc}") from exc
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("items"), list)
            or not isinstance(data.get("next_id"), int)
        ):
            raise DataRecordError(f"Formato inválido em {path}")
        return data

    def _save(self, collection, data):
        path = self._path(collection)
        fd, tmp = tempfile.mkstemp(dir=self.db_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise

    # ---------- User_account ----------
    def add_user(self, user):
        with self._lock:
            data = self._load("users")
            if any(u["email"] == user.email for u in data["items"]):
                raise DuplicateError("email")
            user.id = data["next_id"]
            data["next_id"] += 1
            data["items"].append(user.to_dict())
            self._save("users", data)
            return user

    def find_user_by_email(self, email):
        with self._lock:
            for u in self._load("users")["items"]:
                if u["email"] == email:
                    return User_account.from_dict(u)
        return None

    def find_user_by_id(self, user_id):
        with self._lock:
            for u in self._load("users")["items"]:
                if u["id"] == user_id:
                    return User_account.from_dict(u)
        return None

    # ---------- Disciplina ----------
    def list_disciplinas(self):
        with self._lock:
            return [Disciplina.from_dict(d) for d in self._load("disciplinas")["items"]]

    def get_disciplina(self, disciplina_id):
        with self._lock:
            for d in self._load("disciplinas")["items"]:
                if d["id"] == disciplina_id:
                    return Disciplina.from_dict(d)
        return None

    def add_disciplina(self, disciplina):
        with self._lock:
            data = self._load("disciplinas")
            if any(d["codigo"] == disciplina.codigo for d in data["items"]):
                raise DuplicateError("codigo")
            disciplina.id = data["next_id"]
            data["next_id"] += 1
            data["items"].append(disciplina.to_dict())
            self._save("disciplinas", data)
            return disciplina

    def update_disciplina(self, disciplina_id, changes):
        """Aplica `changes` (dict já validado). Retorna a Disciplina ou None se não existir."""
        with self._lock:
            data = self._load("disciplinas")
            target = next((d for d in data["items"] if d["id"] == disciplina_id), None)
            if target is None:
                return None
            novo_codigo = changes.get("codigo")
            if novo_codigo and any(
                d["codigo"] == novo_codigo and d["id"] != disciplina_id for d in data["items"]
            ):
                raise DuplicateError("codigo")
            target.update(changes)
            self._save("disciplinas", data)
            return Disciplina.from_dict(target)

    def delete_disciplina(self, disciplina_id):
        """Retorna True se removeu, False se não existia."""
        with self._lock:
            data = self._load("disciplinas")
            restantes = [d for d in data["items"] if d["id"] != disciplina_id]
            if len(restantes) == len(data["items"]):
                return False
            data["items"] = restantes
            self._save("disciplinas", data)
            return True
