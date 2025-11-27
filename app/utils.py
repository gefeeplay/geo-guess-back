# Пароли + JWT.

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from passlib.context import CryptContext
from jose import jwt, JWTError

load_dotenv()

# Читаем секрет из переменных окружения (в production обязательно задавать)
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
# Время жизни access token в минутах
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))  

# Используем pbkdf2_sha256 чтобы избежать проблем с bcrypt на Windows
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """Вернуть хэш пароля."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить plain -> hashed."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Создать JWT-token с payload = data. Автоматически добавляет exp."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодировать токен. Возвращает payload или None при ошибке/истёкшем сроке."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
