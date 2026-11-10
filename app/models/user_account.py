"""Model User_account (recurso `portal`).

Guarda os dados do usuário e sabe validar o cadastro e conferir senhas.
A senha nunca é guardada em texto puro: apenas um hash PBKDF2-HMAC-SHA256
com salt aleatório, no formato  pbkdf2_sha256$<iterações>$<salt>$<hash>.
"""
import hashlib
import hmac
import os
import re
import secrets

from app.models.errors import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _iterations():
    return int(os.environ.get("BMVC_PBKDF2_ITER", "200000"))


class User_account:
    def __init__(self, nome, email, senha_hash, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha_hash = senha_hash

    # ---------- validação e criação ----------
    @staticmethod
    def validate_registration(data):
        if not isinstance(data, dict):
            raise ValidationError({"corpo": "Envie um objeto JSON com nome, email e senha."})
        errors = {}
        nome = data.get("nome")
        email = data.get("email")
        senha = data.get("senha")

        if not isinstance(nome, str) or not 2 <= len(nome.strip()) <= 100:
            errors["nome"] = "Obrigatório, texto de 2 a 100 caracteres."
        if not isinstance(email, str) or len(email.strip()) > 254 or not EMAIL_RE.match(email.strip()):
            errors["email"] = "Obrigatório, em formato de e-mail válido."
        if not isinstance(senha, str) or not 8 <= len(senha) <= 128:
            errors["senha"] = "Obrigatória, de 8 a 128 caracteres."
        if errors:
            raise ValidationError(errors)
        return {"nome": nome.strip(), "email": email.strip().lower(), "senha": senha}

    @classmethod
    def create(cls, nome, email, senha):
        return cls(nome=nome, email=email, senha_hash=cls.hash_password(senha))

    # ---------- senha ----------
    @staticmethod
    def hash_password(senha, iterations=None):
        iterations = iterations or _iterations()
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"

    @staticmethod
    def check_hash(senha, stored):
        try:
            algo, iterations, salt, expected = stored.split("$")
            if algo != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256", senha.encode("utf-8"), bytes.fromhex(salt), int(iterations)
            )
        except (ValueError, AttributeError):
            return False
        return hmac.compare_digest(digest.hex(), expected)

    def verify_password(self, senha):
        return self.check_hash(senha, self.senha_hash)

    # ---------- serialização ----------
    def to_dict(self):
        """Representação completa, usada só na persistência (inclui o hash)."""
        return {"id": self.id, "nome": self.nome, "email": self.email, "senha_hash": self.senha_hash}

    def to_public_dict(self):
        """Representação segura para respostas da API (sem o hash)."""
        return {"id": self.id, "nome": self.nome, "email": self.email}

    @classmethod
    def from_dict(cls, d):
        return cls(id=d["id"], nome=d["nome"], email=d["email"], senha_hash=d["senha_hash"])
