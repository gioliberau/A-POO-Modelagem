"""Povoa o banco com disciplinas de EXEMPLO (opcional, só para demonstração).

Os códigos e nomes abaixo são ilustrativos, não refletem a oferta real da FCTE.
Uso:  python seed.py
"""
from app.controllers.datarecord import DataRecord, DuplicateError
from app.models.disciplina import Disciplina

EXEMPLOS = [
    dict(codigo="DEMO0001", nome="Cálculo 1", creditos=6, departamento="Exemplo", curso="Engenharias"),
    dict(codigo="DEMO0002", nome="Orientação a Objetos", creditos=4, departamento="Exemplo", curso="Engenharia de Software"),
    dict(codigo="DEMO0003", nome="Física 1", creditos=4, departamento="Exemplo", curso="Engenharias"),
]

if __name__ == "__main__":
    record = DataRecord()
    for dados in EXEMPLOS:
        try:
            record.add_disciplina(Disciplina(**dados))
            print("inserida:", dados["codigo"])
        except DuplicateError:
            print("já existe:", dados["codigo"])
