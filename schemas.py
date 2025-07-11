# schemas.py
from pydantic import BaseModel
from datetime import date

# --- 클라이언트용 스키마 ---
class LicenseRequest(BaseModel):
    license_key: str
    mac_address: str

class LicenseStatusResponse(BaseModel):
    status: str
    expires_on: str | None = None
    features: list[str] = []

# --- 관리 도구용 스키마 ---
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class LicenseData(BaseModel):
    license_key: str
    expires_on: date
    user_id: str | None = None
    features: list[str] = []
    registered_mac: str | None = None

    class Config:
        from_attributes = True

class CreateLicenseRequest(BaseModel):
    days: int
    user_id: str | None = None

class ExtendLicenseRequest(BaseModel):
    license_key: str
    days: int

class SetExpiryRequest(BaseModel):
    license_key: str
    expires_on: date

class SavePermissionsRequest(BaseModel):
    features: list[str]
    
class ResetMacRequest(BaseModel):
    license_key: str

class SetMacRequest(BaseModel):
    license_key: str
    mac_address: str

# <<<< 추가된 부분 >>>>
class SetUserIdRequest(BaseModel):
    license_key: str
    user_id: str