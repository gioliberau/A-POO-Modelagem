"""Model Disciplina (recurso `banco`).

Atributos: id, codigo (único), nome, creditos, departamento, curso (opcional).
"""
import re

from app.models.errors import ValidationError

CODIGO_RE = re.compile(r"^[A-Z0-9]{3,12}$")
FIELDS = ("codigo", "nome", "creditos", "departamento", "curso")


class Disciplina:
    def __init__(self, codigo, nome, creditos, departamento, curso="", id=None):
        self.id = id
        self.codigo = codigo
        self.nome = nome
        self.creditos = creditos
        self.departamento = departamento
        self.curso = curso

    @staticmethod
    def validate(data, partial=False):
        """Valida e normaliza um payload.

        partial=False (CREATE): codigo, nome, creditos e departamento são obrigatórios.
        partial=True  (UPDATE): só valida os campos enviados; exige ao menos um.
        Campos desconhecidos (inclusive `id`) são ignorados.
        """
        if not isinstance(data, dict):
            raise ValidationError({"corpo": "Envie um objeto JSON."})
        errors, clean = {}, {}

        def present(key):
            return key in data

        if present("codigo") or not partial:
            v = data.get("codigo")
            v = v.strip().upper() if isinstance(v, str) else None
            if v is None or not CODIGO_RE.match(v):
                errors["codigo"] = "Obrigatório, 3 a 12 letras/números (ex.: ABC0001)."
            else:
                clean["codigo"] = v

        if present("nome") or not partial:
            v = data.get("nome")
            if not isinstance(v, str) or not 2 <= len(v.strip()) <= 120:
                errors["nome"] = "Obrigatório, texto de 2 a 120 caracteres."
            else:
                clean["nome"] = v.strip()

        if present("creditos") or not partial:
            v = data.get("creditos")
            if isinstance(v, str) and v.strip().isdigit():
                v = int(v.strip())
            if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 30:
                errors["creditos"] = "Obrigatório, número inteiro entre 1 e 30."
            else:
                clean["creditos"] = v

        if present("departamento") or not partial:
            v = data.get("departamento")
            if not isinstance(v, str) or not 2 <= len(v.strip()) <= 100:
                errors["departamento"] = "Obrigatório, texto de 2 a 100 caracteres."
            else:
                clean["departamento"] = v.strip()

        if present("curso"):
            v = data.get("curso")
            if v is None:
                v = ""
            if not isinstance(v, str) or len(v.strip()) > 100:
                errors["curso"] = "Opcional, texto de até 100 caracteres."
            else:
                clean["curso"] = v.strip()
        elif not partial:
            clean["curso"] = ""

        if partial and not errors and not any(k in data for k in FIELDS):
            errors["corpo"] = "Informe ao menos um campo para atualizar: " + ", ".join(FIELDS) + "."
        if errors:
            raise ValidationError(errors)
        return clean

    def to_dict(self):
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nome": self.nome,
            "creditos": self.creditos,
            "departamento": self.departamento,
            "curso": self.curso,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            codigo=d["codigo"],
            nome=d["nome"],
            creditos=d["creditos"],
            departamento=d["departamento"],
            curso=d.get("curso", ""),
        )
