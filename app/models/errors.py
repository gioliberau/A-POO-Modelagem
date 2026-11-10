class ValidationError(Exception):
    """Dados recebidos não passaram na validação.

    `errors` é um dicionário {campo: mensagem}.
    """

    def __init__(self, errors):
        super().__init__("Dados inválidos")
        self.errors = errors
