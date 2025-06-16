# models.py
from sqlalchemy import Column, Integer, String, Date
from database import Base

# 라이선스 정보를 저장할 'licenses' 테이블 설계도
class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String)
    tier = Column(String, default="basic") # 라이선스 등급 (예: basic, pro)
    expires_on = Column(Date, nullable=False) # 만료일

# 등급별 기능 권한을 저장할 'permissions' 테이블 설계도
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(String, index=True, nullable=False)
    feature_name = Column(String, nullable=False) # 허용 기능 이름 (예: 'like')