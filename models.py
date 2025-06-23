# models.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String)
    expires_on = Column(Date, nullable=False)
    
    # <<<< 추가: 등록된 MAC 주소를 저장할 컬럼 >>>>
    registered_mac = Column(String, nullable=True, index=True)
    
    permissions = relationship("Permission", back_populates="license", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, ForeignKey("licenses.license_key"), nullable=False)
    feature_name = Column(String, nullable=False)
    license = relationship("License", back_populates="permissions")