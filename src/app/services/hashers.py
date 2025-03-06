from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def make_password(password: str):
    password = pwd_context.hash(password)
    return password

def get_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)
