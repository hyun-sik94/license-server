# models.py (수정)
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String)
    expires_on = Column(Date, nullable=False)
    
    # 이 라이선스가 가진 권한 목록을 불러올 수 있도록 관계 설정
    permissions = relationship("Permission", back_populates="license", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, ForeignKey("licenses.license_key"), nullable=False)
    feature_name = Column(String, nullable=False)

    # 이 권한이 속한 라이선스 정보를 불러올 수 있도록 관계 설정
    license = relationship("License", back_populates="permissions")