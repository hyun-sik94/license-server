# database.py (수정)
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Render 환경 변수에 설정된 DATABASE_URL을 가져온다.
# 만약 없으면, 예전 방식인 로컬 sqlite 파일을 사용한다.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./license.sqlite")

# PostgreSQL 주소는 'postgres://'로 시작하는데, SQLAlchemy가 이를 인식하도록 'postgresql://'로 변경해준다.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()