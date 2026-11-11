import hashlib
import hmac
import secrets


def digest_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password):
    salt = secrets.token_bytes(16)
    hashed = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${hashed.hex()}"


def verify_password(password, stored):
    _, salt, expected = stored.split("$")
    candidate = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(candidate.hex(), expected)


def csrf_token(secret):
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(secret.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return f"{nonce}.{signature}"


def valid_csrf(token, secret):
    nonce, _, signature = token.partition(".")
    expected = hmac.new(secret.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return bool(nonce) and hmac.compare_digest(signature, expected)
