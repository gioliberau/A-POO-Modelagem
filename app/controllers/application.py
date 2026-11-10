"""Controller Application do BMVC.

Concentra as regras de negócio dos dois recursos:

  * portal -> cadastro, login, logout e controle de sessão (User_account)
  * banco  -> CRUD de Disciplina, sempre protegido por sessão

Os métodos de API NÃO dependem do Bottle: recebem o conteúdo da requisição
já lido (dict e session_id) e devolvem (status_http, corpo_dict). Quem traduz
isso para HTTP é o route.py. Só `render` usa o Bottle (template engine).
"""
import secrets
import threading
import time

from app.controllers.datarecord import DataRecord, DuplicateError
from app.models.disciplina import Disciplina
from app.models.errors import ValidationError
from app.models.user_account import User_account


def _erro(status, mensagem, **extra):
    corpo = {"erro": mensagem}
    corpo.update(extra)
    return status, corpo


class Application:
    SESSION_TTL = 3600  # segundos

    def __init__(self, record=None, clock=time.time):
        self.record = record or DataRecord()
        self._clock = clock
        self._sessions = {}  # session_id -> (user_id, expira_em)
        self._lock = threading.Lock()
        self._dummy_hash = None

    # ================= PORTAL =================
    def register_user(self, data):
        try:
            clean = User_account.validate_registration(data)
        except ValidationError as exc:
            return _erro(400, "Dados inválidos.", campos=exc.errors)
        user = User_account.create(clean["nome"], clean["email"], clean["senha"])
        try:
            self.record.add_user(user)
        except DuplicateError:
            return _erro(409, "Já existe um usuário com este e-mail.")
        return 201, {"mensagem": "Usuário cadastrado.", "usuario": user.to_public_dict()}

    def login(self, data):
        """Retorna (status, corpo, session_id). session_id só vem preenchido em caso de sucesso."""
        email = data.get("email") if isinstance(data, dict) else None
        senha = data.get("senha") if isinstance(data, dict) else None
        if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha:
            status, corpo = _erro(400, "Informe email e senha.")
            return status, corpo, None

        user = self.record.find_user_by_email(email.strip().lower())
        if user is None:
            # gasta o mesmo tempo de uma verificação real (dificulta enumerar e-mails)
            if self._dummy_hash is None:
                self._dummy_hash = User_account.hash_password("senha-inexistente")
            User_account.check_hash(senha, self._dummy_hash)
            ok = False
        else:
            ok = user.verify_password(senha)
        if not ok:
            status, corpo = _erro(401, "Credenciais inválidas.")
            return status, corpo, None

        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._purge()
            self._sessions[session_id] = (user.id, self._clock() + self.SESSION_TTL)
        return 200, {"mensagem": "Login realizado.", "usuario": user.to_public_dict()}, session_id

    def logout(self, session_id):
        with self._lock:
            self._sessions.pop(session_id, None)
        return 200, {"mensagem": "Sessão encerrada."}

    def current_user(self, session_id):
        """Retorna o dict público do usuário autenticado ou None."""
        if not session_id:
            return None
        with self._lock:
            self._purge()
            entry = self._sessions.get(session_id)
        if entry is None:
            return None
        user = self.record.find_user_by_id(entry[0])
        return user.to_public_dict() if user else None

    def _purge(self):
        agora = self._clock()
        for sid in [s for s, (_, exp) in self._sessions.items() if exp <= agora]:
            del self._sessions[sid]

    # ================= BANCO =================
    def _nao_autenticado(self):
        return _erro(401, "Não autenticado. Faça login em /portal/login.")

    def list_disciplinas(self, session_id):
        if not self.current_user(session_id):
            return self._nao_autenticado()
        itens = [d.to_dict() for d in self.record.list_disciplinas()]
        return 200, {"total": len(itens), "disciplinas": itens}

    def get_disciplina(self, session_id, disciplina_id):
        if not self.current_user(session_id):
            return self._nao_autenticado()
        d = self.record.get_disciplina(disciplina_id)
        if d is None:
            return _erro(404, f"Disciplina {disciplina_id} não encontrada.")
        return 200, {"disciplina": d.to_dict()}

    def create_disciplina(self, session_id, data):
        if not self.current_user(session_id):
            return self._nao_autenticado()
        try:
            clean = Disciplina.validate(data)
        except ValidationError as exc:
            return _erro(400, "Dados inválidos.", campos=exc.errors)
        try:
            d = self.record.add_disciplina(Disciplina(**clean))
        except DuplicateError:
            return _erro(409, f"Já existe uma disciplina com o código {clean['codigo']}.")
        return 201, {"mensagem": "Disciplina cadastrada.", "disciplina": d.to_dict()}

    def update_disciplina(self, session_id, disciplina_id, data):
        if not self.current_user(session_id):
            return self._nao_autenticado()
        try:
            clean = Disciplina.validate(data, partial=True)
        except ValidationError as exc:
            return _erro(400, "Dados inválidos.", campos=exc.errors)
        try:
            d = self.record.update_disciplina(disciplina_id, clean)
        except DuplicateError:
            return _erro(409, f"Já existe outra disciplina com o código {clean['codigo']}.")
        if d is None:
            return _erro(404, f"Disciplina {disciplina_id} não encontrada.")
        return 200, {"mensagem": "Disciplina atualizada.", "disciplina": d.to_dict()}

    def delete_disciplina(self, session_id, disciplina_id):
        if not self.current_user(session_id):
            return self._nao_autenticado()
        if not self.record.delete_disciplina(disciplina_id):
            return _erro(404, f"Disciplina {disciplina_id} não encontrada.")
        return 200, {"mensagem": f"Disciplina {disciplina_id} excluída."}

    # ================= VIEWS (HTML) =================
    def render(self, page, session_id=None, **context):
        """Renderiza uma view de app/views/html/. Retorna None se `banco` sem login."""
        from bottle import template  # import tardio: a lógica acima não depende do Bottle

        if page == "banco":
            user = self.current_user(session_id)
            if not user:
                return None
            context.update(user=user, disciplinas=[d.to_dict() for d in self.record.list_disciplinas()])
        elif page == "portal":
            context.setdefault("msg", None)
            context.setdefault("err", None)
        return template(page, **context)
