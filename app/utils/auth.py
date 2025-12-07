"""
Utility functions for password hashing, JWT token creation, and email verification.
"""
from datetime import datetime, timedelta, timezone
import os
from typing import Optional
from email.mime.text import MIMEText
import smtplib

from passlib.context import CryptContext
from jose import jwt, JWTError
from email_validator import validate_email, EmailNotValidError

SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    Verify a plain password against its hashed version.

    Args:
        plain_password (str): The plain password.
        hashed_password (str): The hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token.

    Args:
        data (dict): The data to encode in the token.
        expires_delta (Optional[timedelta]): Expiration time delta.

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    """
    Decode a JWT access token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict or None: The decoded payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def send_verification_email(email: str, user_id: int):
    """
    Send a verification email to the user.

    Args:
        email (str): The user's email address.
        user_id (int): The user's ID.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    try:
        validate_email(email)
    except EmailNotValidError:
        return False
    verification_link = f"http://localhost:8000/users/verify/{user_id}"
    msg = MIMEText(f"Please verify your email by clicking the following link: {verification_link}")
    msg['Subject'] = 'Verify your email'
    msg['From'] = os.getenv('SMTP_USER')
    msg['To'] = email
    try:
        with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError, ValueError):
        return False
