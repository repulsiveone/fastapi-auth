from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def make_password(password: str):
    password = pwd_context.hash(password)
    return password