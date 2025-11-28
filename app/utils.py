# Пароли + JWT.
import secrets
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from passlib.context import CryptContext
from jose import jwt, JWTError

import smtplib
from email.mime.text import MIMEText

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

def create_verification_token():
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(minutes=30)
    return token, expires


def send_verification_email(email: str, token: str):
    try:
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        
        if not smtp_user or not smtp_pass:
            print("SMTP credentials not configured properly")
            return False
        
        # Проверяем, что это Gmail
        if "gmail.com" not in smtp_user:
            print("Warning: Using Gmail SMTP with non-Gmail account")
        
        verification_url = f"http://localhost:5173/geo-guess-grid/verify?token={token}"
        
        subject = "Verify your email address"
        body = f"""
        Hello!
        
        Please verify your email address by clicking the link below:
        
        {verification_url}
        
        Or use this token: {token}
        
        This link will expire in 30 minutes.
        
        If you didn't create an account, please ignore this email.
        """
        
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = email
        
        print(f"Attempting to send email to {email} via {smtp_user}")
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()  # Обязательно для Gmail
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email, msg.as_string())
        
        print(f"✓ Verification email sent successfully to {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ SMTP Authentication failed: {e}")
        print("Please check:")
        print("1. 2-Step Verification is enabled")
        print("2. App Password is generated correctly")
        print("3. SMTP_PASS is the 16-character app password")
        return False
    except Exception as e:
        print(f"✗ Failed to send email: {e}")
        return False
