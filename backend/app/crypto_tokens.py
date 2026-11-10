"""Colunas criptografadas (Fernet). Sem TOKEN_ENC_KEY no ambiente, grava em texto puro (compatível)."""
import os, sys
from sqlalchemy.types import TypeDecorator, Text

# bibliotecas instaladas em /app/_vendor (pasta montada), assim sobrevivem a recriar o container
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_vendor"))

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # biblioteca ausente
    Fernet = None
    InvalidToken = Exception

_PREFIXO = "enc:"


def _fernet():
    chave = os.getenv("TOKEN_ENC_KEY")
    if not chave or Fernet is None:
        return None
    return Fernet(chave.encode())


class EncryptedText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        f = _fernet()
        if value is None or f is None or str(value).startswith(_PREFIXO):
            return value
        return _PREFIXO + f.encrypt(str(value).encode()).decode()

    def process_result_value(self, value, dialect):
        if value is None or not str(value).startswith(_PREFIXO):
            return value  # texto puro antigo
        f = _fernet()
        if f is None:
            return value
        try:
            return f.decrypt(str(value)[len(_PREFIXO):].encode()).decode()
        except InvalidToken:
            return value
