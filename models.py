# models.py
from sqlalchemy import Column, Integer, String, Date
from database import Base

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String)
    tier = Column(String, default="basic")
    expires_on = Column(Date, nullable=False)

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, index=True)
    tier = Column(String, index=True, nullable=False)
    feature_name = Column(String, nullable=False)