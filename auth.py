import sqlite3
import hashlib
import os

DB_PATH = "users.db"


def init_db():
    """Create the users table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _hash_password(password: str, salt: bytes) -> str:
    """PBKDF2-HMAC-SHA256 password hashing (stdlib only, no extra deps)."""
    return hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100_000
    ).hex()


def create_user(username: str, password: str):
    """
    Create a new user.
    Returns (success: bool, message: str)
    """
    username = username.strip()

    if not username or not password:
        return False, "Username and password cannot be empty."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False, "That username is already taken."

    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)

    c.execute(
        "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
        (username, salt.hex(), password_hash)
    )
    conn.commit()
    conn.close()

    return True, "Account created! You can now log in."


def verify_user(username: str, password: str) -> bool:
    """Check username/password against stored hash. Returns True/False."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT salt, password_hash FROM users WHERE username = ?",
        (username.strip(),)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    salt_hex, stored_hash = row
    salt = bytes.fromhex(salt_hex)
    candidate_hash = _hash_password(password, salt)

    return candidate_hash == stored_hash
