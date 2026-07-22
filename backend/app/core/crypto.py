import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet:
    """
    Crée une instance Fernet en dérivant une clé valide à partir de SECRET_KEY.
    Fernet a besoin d'une clé de 32 octets encodée en base64 url-safe.
    """
    key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)

def encrypt_value(value: str) -> str:
    """
    Chiffre une chaîne de caractères.
    """
    f = get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")

def decrypt_value(encrypted_value: str) -> str:
    """
    Déchiffre une chaîne de caractères chiffrée.
    """
    f = get_fernet()
    return f.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
