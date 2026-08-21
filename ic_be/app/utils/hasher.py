from passlib.context import CryptContext

pwd_context_12 = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_context_04 = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4, deprecated="auto")


def hash_password(password: str):
    return pwd_context_12.hash(password)


def hash_04_password(password: str):
    return pwd_context_04.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context_12.verify(password, hashed_password)


if __name__ == '__main__':
    print(hash_password("123123"))
    hash_pass = hash_04_password("123123")
    print(hash_pass)
    print(
        verify_password("123123", hash_pass)
    )
