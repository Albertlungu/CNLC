"""
./backend/utils/password.py

Password utils to make encryption protection for users.
"""

import bcrypt

def hash_password(password:str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def main():
    return hash_password("")

if __name__ == "__main__":
   print(main())