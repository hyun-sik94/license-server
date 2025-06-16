# hash_password.py
from passlib.context import CryptContext

# 사용할 암호화 방식 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

plain_password = input("암호화할 비밀번호를 입력하세요: ")
hashed_password = pwd_context.hash(plain_password)

print("\n생성된 비밀번호 해시 (이 값을 서버 환경변수에 저장하세요):")
print(hashed_password)